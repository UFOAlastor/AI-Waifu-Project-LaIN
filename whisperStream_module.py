# whisperStream_module.py

import queue
import threading
import pyaudio
import webrtcvad
import numpy as np
import whisper
import wave
import logging
import tempfile
from PyQt5.QtCore import pyqtSignal, QObject

# 配置日志
logger = logging.getLogger("whisperStream_module")
logging.basicConfig(level=logging.DEBUG)


class SpeechStreamRecognition(QObject):
    # 定义信号
    update_text_signal = pyqtSignal(str)  # 用于实时更新识别文本
    recording_ended_signal = pyqtSignal()  # 用于通知录音结束

    def __init__(self, main_settings):
        super().__init__()
        self.settings = main_settings
        self._is_running = False
        self.vad_mode = self.settings.get("vad_mode", 2)
        self.model_name = self.settings.get("model_name", "small")
        self.initial_prompt = self.settings.get(
            "initial_prompt", "以下是普通话为主的句子，这是提交给智能助手的语音输入。"
        )
        self.max_silence_duration = self.settings.get("max_silence_duration", 2)

        # 配置录音参数
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024

        # 创建 VAD 和 Whisper 模型
        self.vad = webrtcvad.Vad(self.vad_mode)
        self.model = whisper.load_model(self.model_name)

        # 初始化音频队列
        self.audio_queue = queue.Queue()
        self.silent_chunks = 0
        self.audio_lock = threading.Lock()

    # 语音检测函数
    def detect_speech(self, audio_data, sample_rate=16000, frame_duration_ms=20):
        frames = self.chunk_audio_data(audio_data, frame_duration_ms, sample_rate)
        for frame in frames:
            frame_bytes = np.array(frame, dtype=np.int16).tobytes()
            if self.vad.is_speech(frame_bytes, sample_rate):
                return True
        return False

    # 修正 chunk_audio_data 方法
    def chunk_audio_data(self, audio_data, frame_duration_ms=20, sample_rate=16000):
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))  # 单帧长度
        frames = [
            audio_data[i : i + frame_size]
            for i in range(0, len(audio_data) - frame_size + 1, frame_size)
        ]
        return frames

    # 录音线程
    def audio_producer(self):
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
            )
            logger.debug("录音线程启动")
            while self._is_running:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                self.audio_queue.put(data)
            stream.stop_stream()
            stream.close()
            audio.terminate()
            logger.debug("录音线程停止")
        except Exception as e:
            logger.error(f"录音线程异常: {e}")

    # 音频处理线程
    def audio_consumer(self):
        temp_frames = []
        while True:
            try:
                data = self.audio_queue.get(timeout=0.1)
                # 在 audio_consumer 方法中：
                if len(data) == 0:
                    logger.warning("收到空帧，跳过处理")
                    continue

                # 检测静音
                is_speech = self.detect_speech(np.frombuffer(data, dtype=np.int16))
                if not is_speech:
                    self.silent_chunks += 1
                    self.transcribe_and_log(temp_frames)
                    temp_frames.clear()
                else:
                    self.silent_chunks = 0
                    temp_frames.append(data)  # 仅仅在非静音时才输入

                # 静音超时，停止录音
                if not self._is_running or self.silent_chunks > (
                    self.RATE / self.CHUNK * self.max_silence_duration
                ):
                    if self._is_running:
                        logger.info("检测到持续静音，结束录音")
                    else:
                        logger.info("手动触发，结束录音")
                    self._is_running = False
                    self.recording_ended_signal.emit()  # 通知录音结束
                    break

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"音频处理异常: {e}")
                break

    # 转录并记录
    def transcribe_and_log(self, frames):
        audio_data = b"".join(frames)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            with wave.open(temp_wav, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.RATE)
                wf.writeframes(audio_data)
            result = self.model.transcribe(
                temp_wav.name, initial_prompt=self.initial_prompt
            )
            if result["text"]:
                logger.debug(f"实时转录结果: {result['text']}")
                self.update_text_signal.emit(result["text"])  # 发出实时更新信号

    # 启动流式语音识别
    def start_streaming(self):
        self._is_running = True
        producer_thread = threading.Thread(target=self.audio_producer)
        consumer_thread = threading.Thread(target=self.audio_consumer)
        producer_thread.start()
        consumer_thread.start()
        producer_thread.join()
        consumer_thread.join()

    # 停止流式语音识别
    def stop_streaming(self):
        self._is_running = False
        logger.debug("停止流式语音识别")


if __name__ == "__main__":
    import json

    with open("./config.json", "r", encoding="utf-8") as f:
        settings = json.load(f)

    recognizer = SpeechStreamRecognition(settings)
    recognizer.start_streaming()
