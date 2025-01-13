# asr_module.py

import numpy as np
import queue, threading
import pyaudio, webrtcvad, wave, tempfile
from PyQt5.QtCore import pyqtSignal, QObject
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
import logging

# 配置日志
logger = logging.getLogger("asr_module")


class SpeechRecognition(QObject):
    # 定义信号
    update_text_signal = pyqtSignal(str)  # 用于实时更新识别文本
    recording_ended_signal = pyqtSignal()  # 用于通知录音结束
    detect_speech_signal = pyqtSignal(bool)  # 用于通知检测到人声

    def __init__(self, main_settings):
        super().__init__()
        self.settings = main_settings
        self._is_running = False
        self.vad_mode = self.settings.get("vad_mode", 2)
        self.webrtc_aec = self.settings.get("webrtc_aec", False)  # UNDO AEC回声剔除
        self.auto_send_silence_time = self.settings.get("auto_send_silence_time", 3)

        # 配置录音参数
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024

        # 创建 VAD 模型
        self.vad = webrtcvad.Vad(self.vad_mode)

        # 初始化 SenseVoice 模型
        model_dir = self.settings.get("model_dir", "./SenseVoiceSmall")
        self.model = AutoModel(
            model=model_dir,
            trust_remote_code=True,
            device="cuda:0",  # 默认使用 GPU
        )

        self.silence_timer = 0  # 静默时间累积
        self.audio_buffer = []  # 用于暂存有效语音数据
        self.transcribe_but_not_send = False  # 已经识别但是未发送

        # 初始化音频队列
        self.audio_queue = queue.Queue()
        self.audio_lock = threading.Lock()

    def detect_speech(self, audio_data, sample_rate=16000, frame_duration_ms=20):
        """
        使用 WebRTC VAD 检测音频数据是否包含有效语音。
        """
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))  # 单帧长度
        frames = [
            audio_data[i : i + frame_size]
            for i in range(0, len(audio_data) - frame_size + 1, frame_size)
        ]

        # 累计检测结果
        active_segments = 0
        total_segments = len(frames)

        for frame in frames:
            frame_bytes = np.array(frame, dtype=np.int16).tobytes()
            if self.vad.is_speech(frame_bytes, sample_rate):  # 检测是否有语音
                active_segments += 1

        # 判定语音激活率
        activation_rate = active_segments / total_segments
        return activation_rate >= 0.4  # 有效激活率 >= 40%

    # 录音线程
    def audio_producer(self):
        """麦克风收音函数 (音频生产者)"""
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
            )
            logger.debug("audio_producer录音线程启动")
            while self._is_running:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                self.audio_queue.put(data)
            stream.stop_stream()
            stream.close()
            audio.terminate()
            logger.debug("audio_producer录音线程停止")
        except Exception as e:
            logger.error(f"audio_producer录音线程异常: {e}")
        logger.debug("audio_producer正常退出")

    def audio_consumer(self):
        """
        处理音频队列中的数据, 按500ms段进行检测, 并根据检测结果处理静默时长. (音频消费者)
        """
        temp_frames = []
        chunk_duration_ms = 20  # 每个检测段的持续时间
        frame_window_ms = 500  # 检测时间段（500ms）
        frames_per_window = frame_window_ms // chunk_duration_ms  # 每个时间段的帧数

        while self._is_running:
            try:
                data = self.audio_queue.get(timeout=0.1)
                if len(data) == 0:
                    logger.warning("audio_producer收到空帧，跳过处理")
                    continue

                # 缓存音频帧
                temp_frames.append(np.frombuffer(data, dtype=np.int16))

                # 检测 500ms 的音频数据
                if len(temp_frames) * self.CHUNK >= self.RATE * (
                    frame_window_ms / 1000
                ):
                    # 合并数据并检测
                    merged_frames = np.concatenate(temp_frames[:frames_per_window])
                    is_active = self.detect_speech(merged_frames)
                    temp_frames = temp_frames[frames_per_window:]  # 移动窗口

                    if is_active:
                        # 检测到语音，重置静默计时器，存储音频数据
                        self.detect_speech_signal.emit(self._is_running)
                        self.silence_timer = 0
                        self.audio_buffer.append(merged_frames)
                        # logger.debug("检测到有效语音，加入缓存")
                    else:
                        # 检测到静默，累积静默时间
                        self.detect_speech_signal.emit(False)
                        self.silence_timer += frame_window_ms / 1000.0  # 转为秒

                        if self.audio_buffer:  # 如果音频缓存非空, 就进行一次识别
                            self.audio_transcribe(self.audio_buffer)
                            self.audio_buffer = []  # 清空缓存

                        if (  # 静默时间超限并且存在未发送内容
                            self.transcribe_but_not_send
                            and self.silence_timer >= self.auto_send_silence_time
                            and self.auto_send_silence_time != -1
                        ):
                            logger.info("静默时间超限，触发结果发送")
                            self.transcribe_but_not_send = False  # 重置未发送标志
                            self.recording_ended_signal.emit()
                            self.silence_timer = 0  # 重置静默计时器
                    continue

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"audio_consumer音频处理异常: {e}")
                break
        logger.debug("audio_consumer正常退出")

    # 转录并记录
    def audio_transcribe(self, frames):
        """对包含人声的音频序列进行语音识别"""
        audio_data = b"".join(frames)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            with wave.open(temp_wav, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.RATE)
                wf.writeframes(audio_data)
            res = self.model.generate(
                input=temp_wav.name,
                cache={},
                language="auto",  # 自动检测语言
                use_itn=True,
            )
            if res and res[0]["text"]:
                text = rich_transcription_postprocess(res[0]["text"])
                logger.debug(f"实时转录结果: {text}")
                self.transcribe_but_not_send = True
                self.update_text_signal.emit(text)

    # 启动流式语音识别
    def start_streaming(self):
        """语音识别线程启动函数"""
        if not self._is_running:
            logger.info("启动流式语音识别")
            self._is_running = True
            self.silence_timer = 0
            self.audio_buffer = []
            self.audio_queue.queue.clear()
            self.transcribe_but_not_send = False
            producer_thread = threading.Thread(target=self.audio_producer)
            consumer_thread = threading.Thread(target=self.audio_consumer)
            producer_thread.start()
            consumer_thread.start()
            producer_thread.join()
            consumer_thread.join()
        else:
            logger.info("流式语音识别已经启动")

    # 停止流式语音识别
    def stop_streaming(self):
        """语音识别线程终止函数"""
        self._is_running = False
        if self.transcribe_but_not_send:  # 存在未发送内容
            logger.info("手动点击按钮，触发语音转录")
            self.recording_ended_signal.emit()
            self.transcribe_but_not_send = False  # 重置未发送标志
            self.silence_timer = 0  # 重置静默计时器
        logger.info("停止流式语音识别")


if __name__ == "__main__":
    import yaml

    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    recognizer = SpeechRecognition(settings)
    recognizer.start_streaming()
