import pyaudio
import numpy as np
import webrtcvad
import whisper
import wave
import tempfile

import logging

# 获取根记录器
logger = logging.getLogger("whisper_module")


class SpeechRecognition:
    def __init__(self, main_settings):
        # 通过配置文件传入的参数
        self._is_running = False  # 非阻塞打断

        self.settings = main_settings
        self.vad_mode = self.settings.get("vad_mode", 2)  # 默认使用模式2
        self.model_name = self.settings.get(
            "model_name", "small"
        )  # 默认使用whisper的small模型
        self.initial_prompt = self.settings.get(
            "initial_prompt", "以下是普通话为主的句子，这是提交给智能助手的语音输入。"
        )  # 默认使用whisper的small模型
        self.max_silence_duration = self.settings.get(
            "max_silence_duration", 2
        )  # 触发录音终止的持续静音时长

        # 配置录音参数
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.MAX_SILENCE_DURATION = self.max_silence_duration

        # 创建 VAD 对象
        self.vad = webrtcvad.Vad(self.vad_mode)

        # 加载 Whisper 模型
        self.model = whisper.load_model(self.model_name)

        # 初始化状态
        self.audio = None
        self.stream = None

    # 语音检测函数
    def detect_speech(self, audio_data, sample_rate=16000, frame_duration_ms=20):
        frames = self.chunk_audio_data(audio_data, frame_duration_ms, sample_rate)
        for frame in frames:
            frame_bytes = np.array(frame, dtype=np.int16).tobytes()
            try:
                if self.vad.is_speech(frame_bytes, sample_rate):
                    return True
            except:
                pass
        return False

    # 将音频数据切分成固定时长的帧
    def chunk_audio_data(self, audio_data, frame_duration_ms=20, sample_rate=16000):
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
        frames = [
            audio_data[i : i + frame_size]
            for i in range(0, len(audio_data), frame_size)
        ]
        return frames

    # 启动录音
    def start_recording(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )
        logger.debug("录音中...")

    # 停止录音
    def stop_recording(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        logger.debug("停止录音")

    # 录音并检测静音
    def record_audio_with_vad_and_energy(self):
        frames = []
        silent_chunks = 0
        total_chunks = 0

        while self._is_running:
            data = self.stream.read(self.CHUNK)

            # 检测是否为语音
            is_speech = self.detect_speech(np.frombuffer(data, dtype=np.int16))

            # 如果检测到语音，保存数据
            frames.append(data)
            total_chunks += 1

            # 如果没有语音检测到，则认为是静音
            if not is_speech:
                silent_chunks += 1
            else:
                silent_chunks = 0  # 有语音输入，重置静音计数

            # 如果达到静音时间阈值，提前结束录音
            if silent_chunks > (self.RATE / self.CHUNK * self.MAX_SILENCE_DURATION):
                logger.info("检测到持续静音，录音结束")
                self._is_running = False
                break

        # 返回录音的音频数据
        return b"".join(frames)

    # 使用 Whisper 进行语音识别
    def transcribe_audio(self, audio_data):
        # 创建一个临时的 .wav 文件，并将音频数据写入其中
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            with wave.open(temp_wav, "wb") as wf:
                wf.setnchannels(1)  # 单声道
                wf.setsampwidth(2)  # 每个样本占2字节
                wf.setframerate(self.RATE)
                wf.writeframes(audio_data)

            # 使用 whisper 进行语音识别
            result = self.model.transcribe(
                temp_wav.name, initial_prompt=self.initial_prompt
            )

            # 获取转录文本
            return result["text"]

    # 启动语音输入并返回识别的文本
    def start_speech_input(self):
        # 开始录音
        self.start_recording()

        # 录制音频并转录
        self._is_running = True
        audio_data = self.record_audio_with_vad_and_energy()

        # 停止录音
        self.stop_recording()

        # 转录并返回结果
        transcribed_text = self.transcribe_audio(audio_data)
        return transcribed_text

    # 打断语音输入
    def stop_speech_input(self):
        # 停止录音
        self._is_running = False
        logger.debug("打断录音")


if __name__ == "__main__":
    import json
    import logging_config

    # 初始化日志配置
    logging_config.setup_logging()

    # 示例配置
    with open("./config.json", "r", encoding="utf-8") as f:
        settings = json.load(f)

    # 创建 SpeechRecognition 实例并初始化
    speech_recognizer = SpeechRecognition(settings)

    # 启动语音输入并获取文本结果
    transcribed_text = speech_recognizer.start_speech_input()
    logger.debug(f"识别结果: {transcribed_text}")
