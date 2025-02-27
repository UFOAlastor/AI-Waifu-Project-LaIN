# asr_module.py

import numpy as np
import queue, threading
from collections import deque
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


class SpeechRecognition(QObject):
    # 定义信号
    update_text_signal = pyqtSignal(tuple)  # 用于传递二元组 (用户名称, 文本)
    recording_ended_signal = pyqtSignal()  # 用于通知录音结束
    detect_speech_signal = pyqtSignal(bool)  # 用于通知检测到人声

    def __init__(self, main_settings):
        """语音识别类初始化

        Args:
            main_settings (dict): 配置文件读取后得到的dict
        """
        super().__init__()
        self.settings = main_settings
        self._is_running = False
        self.asr_vad_mode = gcww(self.settings, "asr_vad_mode", 2, logger)
        self.asr_webrtc_aec = gcww(  # UNDO AEC回声剔除
            self.settings, "asr_webrtc_aec", False, logger
        )
        self.asr_auto_send_silence_time = gcww(
            self.settings, "asr_auto_send_silence_time", 3, logger
        )

        # 创建声纹识别工具对象
        self.vpr = VoicePrintRecognition(main_settings)

        # 配置录音参数
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024

        # 初始化 Silero VAD 模型
        self.vad_model = load_silero_vad()

        # 初始化 SenseVoice 模型
        model_dir = gcww(self.settings, "asr_model_dir", "./SenseVoiceSmall", logger)
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

        logger.debug(f"检测到{len(speech_segments)}个语音段")

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
        self.silence_timer = 0
        self.audio_buffer = deque()
        temp_frames = deque()
        chunk_duration_ms = 20  # 每个检测段的持续时间
        frame_window_ms = 240  # VAD检测时间段
        frames_per_window = frame_window_ms // chunk_duration_ms  # 每个时间段的帧数

        # 定义累积语音的时长阈值
        vprcheck_duration_ms = 480  # 每次声纹检测的窗口大小 (毫秒)
        vpr_temp_frames = deque()
        flag_vprcheck_start = False

        while self._is_running:
            try:
                data = self.audio_queue.get(timeout=0.1)
                if len(data) == 0:
                    logger.warning("audio_producer收到空帧，跳过处理")
                    continue

                # 缓存音频帧
                temp_frames.append(np.frombuffer(data, dtype=np.int16))
                self.audio_buffer.append(np.frombuffer(data, dtype=np.int16))

                # 保持temp_frames的大小不超过frames_per_window
                if len(temp_frames) > frames_per_window:
                    temp_frames.popleft()

                # 只有当temp_frames填满时才进行VAD检测
                if len(temp_frames) == frames_per_window:
                    vad_merged_frames = np.concatenate(temp_frames)
                    is_active = self.detect_speech(vad_merged_frames)

                    if is_active:
                        vpr_temp_frames.append(vad_merged_frames)
                        if (
                            len(vpr_temp_frames) * chunk_duration_ms
                            >= vprcheck_duration_ms
                        ):
                            temp_user = self.vpr.match_voiceprint(vpr_temp_frames)
                            if (
                                self.vpr.vpr_match_only is None
                                or not any(self.vpr.vpr_match_only)
                                or temp_user in self.vpr.vpr_match_only
                            ):
                                self.detect_speech_signal.emit(True)
                                logger.debug("检测到注册用户发言")
                                self.silence_timer = 0
                                if not flag_vprcheck_start:
                                    flag_vprcheck_start = True
                                # 不需要清空audio_buffer，这样可以避免音频被掐头
                            else:
                                self.silence_timer += (
                                    vprcheck_duration_ms / 1000.0
                                )  # 转为秒
                            # 保持vpr_temp_frames的大小不超过vprcheck_duration_ms
                            if (
                                len(vpr_temp_frames) * chunk_duration_ms
                                > vprcheck_duration_ms
                            ):
                                vpr_temp_frames.popleft()
                    else:
                        # 检测到静默，累积静默时间
                        self.detect_speech_signal.emit(False)
                        self.silence_timer += frame_window_ms / 1000.0  # 转为秒

                        if self.audio_buffer:
                            temp_user = self.vpr.match_voiceprint(self.audio_buffer)
                            if (
                                self.vpr.vpr_match_only is None
                                or not any(self.vpr.vpr_match_only)
                                or temp_user in self.vpr.vpr_match_only
                            ):
                                self.audio_transcribe(
                                    temp_user, list(self.audio_buffer)
                                )
                            flag_vprcheck_start = False
                            vpr_temp_frames.clear()
                            self.audio_buffer.clear()

                        if (
                            self.transcribe_but_not_send
                            and self.silence_timer >= self.asr_auto_send_silence_time
                            and self.asr_auto_send_silence_time != -1
                        ):
                            logger.info("静默时间超限，触发结果发送")
                            self.transcribe_but_not_send = False  # 重置未发送标志
                            self.recording_ended_signal.emit()
                            self.silence_timer = 0  # 重置静默计时器
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"audio_consumer音频处理异常: {e}")
                break
        logger.debug("audio_consumer正常退出")

    # 转录并记录
    def audio_transcribe(self, user_name, frames):
        """对包含人声的音频序列进行语音识别

        Args:
            user_name (str): 说话者用户名称
            frames (NDArray): 音频序列
        """
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
                ban_emo_unk=True,  # 情感表情输出
            )
            if res and res[0]["text"]:
                text = rich_transcription_postprocess(res[0]["text"])
                logger.debug(f"实时转录结果: {text}")
                self.transcribe_but_not_send = True
                self.update_text_signal.emit((user_name, text))

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
    import yaml, logging_config

    # 初始化日志配置
    logging_config.setup_logging()

    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    recognizer = SpeechRecognition(settings)
    recognizer.start_streaming()
