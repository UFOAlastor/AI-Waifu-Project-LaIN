# asr_module.py

import copy
import numpy as np
import queue, threading
import pyaudio, wave, tempfile
from silero_vad import load_silero_vad, get_speech_timestamps
from PyQt5.QtCore import pyqtSignal, QObject
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
import logging
from logging_config import gcww

# 配置日志
logger = logging.getLogger("asr_module")

from vpr_module import VoicePrintRecognition
from vits_module import vitsSpeaker


class SpeechRecognition(QObject):
    # 定义信号
    update_text_signal = pyqtSignal(tuple)  # 用于传递二元组 (音频序列, 文本)
    recording_ended_signal = pyqtSignal()  # 用于通知录音结束
    detect_speech_signal = pyqtSignal(bool)  # 用于通知检测到人声

    def __init__(self, main_settings):
        """语音识别类初始化

        Args:
            main_settings (dict): 配置文件读取后得到的dict
        """
        super().__init__()
        self.settings = main_settings
        self.asr_auto_send_silence_time = gcww(
            self.settings, "asr_auto_send_silence_time", 2.7, logger
        )
        model_dir = gcww(self.settings, "asr_model_dir", "./SenseVoiceSmall", logger)

        # 配置录音参数
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024

        # 初始化 Silero VAD 模型
        self.vad_model = load_silero_vad()

        # 初始化 SenseVoice 模型
        self.asr_model = AutoModel(
            model=model_dir,
            trust_remote_code=True,
            device="cuda:0",  # 默认使用 GPU
        )

        # 初始化声纹管理器
        self.vpr_manager = VoicePrintRecognition(main_settings)
        # 初始化vitsSpeaker
        self.vits_speaker = vitsSpeaker(main_settings)

        # 连接 vitsSpeaker 的音频播放结束信号
        self.vits_speaker.audio_start_play.connect(self.on_audio_start_play)
        self.vits_speaker.audio_played.connect(self.on_audio_played)

        # 初始化标志量
        self._is_running = False  # 是否正在运行
        self.audio_buffer_startup = True  # 是否允许开始记录audio_buffer
        self.transcribe_but_not_send = False  # 已经识别但是未发送

        # 初始化音频队列
        self.audio_queue = queue.Queue()
        self.audio_lock = threading.Lock()

    def on_audio_start_play(self):
        self.audio_buffer_startup = False
        logger.debug(f"vits音频播放开始: {self.audio_buffer_startup}")

    def on_audio_played(self):
        self.audio_buffer_startup = True
        logger.debug(f"vits音频播放结束: {self.audio_buffer_startup}")

    def detect_speech(self, audio_data, sample_rate=16000):
        """使用 WebRTC VAD 检测音频数据是否包含有效语音。

        Args:
            audio_data (np.ndarray): 单通道16kHz音频数据（int16或float32格式）
            sample_rate (int): 必须为16000

        Returns:
            bool: 是否检测到人声
        """
        # 数据预处理
        if not isinstance(audio_data, np.ndarray) or audio_data.size == 0:
            return False

        # 格式标准化（int16转float32）
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0

        # 语音段检测（阈值建议0.3-0.5）
        speech_segments = get_speech_timestamps(
            audio_data,
            self.vad_model,
            sampling_rate=sample_rate,
            threshold=0.3,
            return_seconds=True,
        )

        return len(speech_segments) > 0

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
        处理音频队列中的数据, 按frame_window_ms进行检测, 并根据检测结果处理静默时长. (音频消费者)
        """
        silence_timer = 0  # 秒
        audio_buffer = []
        temp_frames = []  # 缓存两倍检测窗口数据
        frames_per_window = 16  # 每个时间段的帧数
        frame_window_ms = frames_per_window * (self.CHUNK / self.RATE) * 1000.0

        while self._is_running:
            try:
                data = self.audio_queue.get(timeout=0.1)
                if len(data) == 0:
                    logger.warning("audio_producer收到空帧，跳过处理")
                    continue

                # 转换数据格式
                frame = np.frombuffer(data, dtype=np.int16)

                # 缓存音频帧到临时帧
                temp_frames.append(frame)
                if self.audio_buffer_startup:
                    logger.debug("记录audio_buffer")
                    audio_buffer.append(frame)

                # 保持temp_frames的大小不超过两倍frames_per_window
                if len(temp_frames) > 2 * frames_per_window:
                    temp_frames.pop(0)

                # 只有当temp_frames达到检测窗口大小才进行VAD检测
                if len(temp_frames) >= frames_per_window:
                    is_active = self.detect_speech(
                        np.concatenate(temp_frames[-frames_per_window:])
                    )

                    if is_active:
                        user_name = self.vpr_manager.match_voiceprint(
                            temp_frames[-frames_per_window:]
                        )
                        if user_name != "Unknown":  # 声纹已注册, 发送语音检测信号量
                            self.detect_speech_signal.emit(True)
                            if not self.audio_buffer_startup:  # 若还没启动audio_buffer
                                self.audio_buffer_startup = True  # 开始记录audio_buffer
                                audio_buffer = temp_frames[:frames_per_window]  # 留缓存
                        silence_timer = 0
                    else:
                        # 检测到静默，累积静默时间
                        self.detect_speech_signal.emit(False)
                        silence_timer += (
                            frame_window_ms / frames_per_window
                        ) / 1000.0  # 转为秒
                        logger.debug(f"silence_timer: {silence_timer}")
                        if audio_buffer:
                            # 只要检测到人声就进行语音识别
                            if self.detect_speech(np.concatenate(audio_buffer)):
                                self.audio_transcribe(audio_buffer)
                                audio_buffer.clear()
                            else:
                                audio_buffer.pop(0)  # 移除最旧的帧
                        if (
                            silence_timer >= self.asr_auto_send_silence_time
                            and self.transcribe_but_not_send
                            and self.asr_auto_send_silence_time != -1
                        ):
                            logger.info("静默时间超限，触发结果发送")
                            self.recording_ended_signal.emit()
                            self.transcribe_but_not_send = False  # 重置未发送标志
                            self._is_running = False  # 结束循环
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"audio_consumer音频处理异常: {e}")
                break
        logger.debug("audio_consumer正常退出")

    # 转录并记录
    def audio_transcribe(self, frames):
        """对包含人声的音频序列进行语音识别

        Args:
            frames (NDArray): 音频序列
        """
        audio_data = b"".join(frames)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            with wave.open(temp_wav, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.RATE)
                wf.writeframes(audio_data)
            res = self.asr_model.generate(
                input=temp_wav.name,
                cache={},
                language="auto",  # 自动检测语言
                use_itn=True,
                ban_emo_unk=True,  # 情感表情输出
            )
            if res and res[0]["text"]:
                text = rich_transcription_postprocess(res[0]["text"])
                logger.debug(f"实时转录结果: {text}")
                self.transcribe_but_not_send = True
                copied_frames = copy.deepcopy(frames)  # 使用深拷贝传递数据
                self.update_text_signal.emit((copied_frames, text))

    # 启动流式语音识别
    def start_streaming(self):
        """语音识别线程启动函数"""
        if not self._is_running:
            logger.info("启动流式语音识别")
            self.audio_queue.queue.clear()
            self._is_running = True
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
        logger.info("停止流式语音识别")


if __name__ == "__main__":
    import yaml, logging_config

    # 初始化日志配置
    logging_config.setup_logging()

    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    recognizer = SpeechRecognition(settings)
    recognizer.start_streaming()
