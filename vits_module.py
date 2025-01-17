# vits_module.py

import requests, re
from io import BytesIO
import pydub, time, pygame, threading
from PyQt5.QtCore import pyqtSignal, QObject
from lipsync_module import WavHandler
import logging

# 获取根记录器
logger = logging.getLogger("vits_module")


class vitsSpeaker(QObject):
    # 声明音频播放完成的信号
    audio_played = pyqtSignal()
    audio_start_play = pyqtSignal()
    audio_lipsync_signal = pyqtSignal(float)

    def __init__(self, main_settings):
        super().__init__()
        """加载配置文件"""
        # 更新配置文件中的 API_URL 和 SPEAKER_ID
        self.API_URL = main_settings.get(
            "vits_api_url", "http://127.0.0.1:23456/voice/vits"
        )
        self.SPEAKER_ID = main_settings.get("SPEAKER_ID", 4)
        self.CLEAN_TEXT = main_settings.get("vits_clean_text", True)

        # 控制停止播放音频事件
        self.stop_event = threading.Event()
        # 音频播放线程
        self.audio_thread = None
        self.wav_handler = WavHandler()  # 添加WavHandler实例

    def get_audio_stream(
        self, text, speaker_id=None, lang="jp", format="wav", length=1.0
    ):
        """发送请求并获取音频流"""
        speaker_id = speaker_id or self.SPEAKER_ID  # 默认使用 SPEAKER_ID
        params = {
            "text": text,
            "id": speaker_id,
            "lang": lang,
            "format": format,
            "length": length,
        }

        try:
            response = requests.get(self.API_URL, params=params, stream=True)

            # 判断请求是否成功
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"音频请求失败，状态码: {response.status_code}")
                return None

        except requests.RequestException as e:
            logger.error(f"请求发生错误: {e}")
            return None

    def play_audio(self, audio_data):
        """播放音频"""
        try:
            audio = pydub.AudioSegment.from_wav(BytesIO(audio_data))
            pygame.mixer.init(frequency=audio.frame_rate)  # 初始化pygame的音频播放
            pygame.mixer.music.load(BytesIO(audio_data))  # 加载音频数据
            pygame.mixer.music.play()  # 播放音频

            # 开始播放音频发出型号
            self.audio_start_play.emit()

            self.wav_handler.Start(audio_data)  # 开始处理音频数据

            while pygame.mixer.music.get_busy():
                if self.stop_event.is_set():
                    logger.info("音频播放已被打断")
                    break
                if not self.wav_handler.Update():
                    break  # 音频播放结束
                else:
                    self.audio_lipsync_signal.emit(self.wav_handler.GetRms())
                    logger.debug(f"语音响度: {self.wav_handler.GetRms()}")
                time.sleep(0.1)

            # 播放完成后发出信号
            self.audio_played.emit()

        except Exception as e:
            logger.error(f"播放音频发生错误: {e}")

    def vits_play(self, text, speaker_id=None, lang="jp", format="wav", length=1.0):
        """输入文本，生成并播放音频"""
        if self.CLEAN_TEXT:  # 文本清洗，移除不适合朗读的内容
            text = self.clean_text_for_vits(text)
            logger.debug(f"文本清洗结果: {text}")

        try:
            audio_data = self.get_audio_stream(text, speaker_id, lang, format, length)

            if audio_data is None:
                logger.error("生成音频失败，无法播放。")
                return

            logger.info("音频生成成功，正在播放...")

            # 如果已有播放线程，先停止之前的播放
            if self.audio_thread and self.audio_thread.is_alive():
                logger.info("正在停止之前的音频播放...")
                self.vits_stop_audio()

            # 创建一个新的线程来播放音频，这样主程序就不会被阻塞
            self.stop_event.clear()  # 清除停止事件，准备播放新音频
            self.audio_thread = threading.Thread(
                target=self.play_audio, args=(audio_data,)
            )
            self.audio_thread.start()

            logger.debug("主程序继续执行，音频正在播放...")

        except Exception as e:
            logger.error(f"发生错误: {e}")

    def vits_stop_audio(self):
        """停止音频播放"""
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()  # 停止播放音频
            self.stop_event.set()  # 设置停止事件
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join()  # 等待音频播放线程安全停止
            logger.info("音频播放已被停止")

    def clean_text_for_vits(self, text):
        """
        精确清洗文本，移除不适合朗读的内容。
        """
        # 定义精确匹配的正则模式
        patterns = [
            r"https?://[a-zA-Z0-9./?=&_%+-]+",
        ]

        # 依次应用所有正则表达式清理文本
        for pattern in patterns:
            text = re.sub(pattern, "", text)

        # 清理多余的空格
        text = re.sub(r"\s+", " ", text).strip()

        return text


# 测试生成和播放音频
if __name__ == "__main__":
    import logging_config, yaml

    # 初始化日志配置
    logging_config.setup_logging()
    # 加载配置文件
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
        vits_speaker = vitsSpeaker(settings)

    # 要合成的日语文本
    text = "今日はとても楽しい一日だったよ～！シアロ～(∠・ω< )⌒☆ 何か面白いことがあったら教えてね！"

    # 调用合成并播放的功能
    vits_speaker.vits_play(text)
