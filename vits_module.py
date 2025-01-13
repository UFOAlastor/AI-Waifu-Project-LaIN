# vits_module.py

import requests
import pydub
from io import BytesIO
import time
import pygame  # 用于播放音频
import yaml
import threading
import re
from PyQt5.QtCore import pyqtSignal, QObject
import logging

# 获取根记录器
logger = logging.getLogger("vits_module")


class vitsSpeaker(QObject):
    # 声明音频播放完成的信号
    audio_played = pyqtSignal()

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

    def get_audio_stream(
        self, text, speaker_id=None, lang="zh", format="wav", length=1.0
    ):
        """发送请求并获取音频流"""
        speaker_id = (
            speaker_id or self.SPEAKER_ID
        )  # 如果未传入speaker_id，使用默认的SPEAKER_ID
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

            # 等待音频播放完成或被打断
            while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                time.sleep(0.1)

            if self.stop_event.is_set():
                logger.info("音频播放已被打断")

            # 播放完成后发出信号
            self.audio_played.emit()

        except Exception as e:
            logger.error(f"播放音频发生错误: {e}")

    def vits_play(self, text, speaker_id=None, lang="zh", format="wav", length=1.0):
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

            # 创建一个新的线程来播放音频，这样主程序就不会被阻塞
            audio_thread = threading.Thread(target=self.play_audio, args=(audio_data,))
            audio_thread.start()

            # 继续执行其他任务
            logger.debug("主程序继续执行，音频正在播放...")

        except Exception as e:
            logger.error(f"发生错误: {e}")

    def vits_stop_audio(self):
        """停止音频播放"""
        if pygame.mixer.get_init():  # 确保pygame.mixer已经初始化
            if pygame.mixer.music.get_busy():  # 确保有音频正在播放
                pygame.mixer.music.stop()  # 停止播放音频
                self.stop_event.set()  # 通知播放线程停止
                logger.info("音频播放已被停止")

    def clean_text_for_vits(self, text):
        """
        精确清洗文本，移除不适合朗读的内容。
        """
        # 定义精确匹配的正则模式
        patterns = [
            r"https?://[a-zA-Z0-9./?=&_%+-]+",  # 精确匹配URL链接
            # r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # 精确匹配电子邮件地址
            # r'([a-zA-Z]:)?(\\[^\s\\/:*?"<>|]+)+\\?',  # 精确匹配Windows文件路径
            # r"<[^>]+>",  # HTML标签（只移除尖括号包裹的内容）
            # r"\*\*[^*]+\*\*|__[^_]+__",  # Markdown加粗语法（**加粗**或__加粗__）
            # r"\d{10,}",  # 长数字串（10位或以上）
            # r"[a-f0-9-]{32,}",  # UUID（32位或以上的十六进制串，带或不带连字符）
            # r"[{}]{1,2}.*?[{}]{1,2}",  # 花括号包裹的内容，如`{占位符}`或`{{占位符}}`
            # r"`[^`]+`",  # Markdown行内代码语法（`代码`）
            # r"--[a-zA-Z0-9_]+(=[^ ]+)?",  # 命令行参数，如 --arg=value
        ]

        # 依次应用所有正则表达式清理文本
        for pattern in patterns:
            text = re.sub(pattern, "", text)

        # 清理多余的空格
        text = re.sub(r"\s+", " ", text).strip()

        return text


# 测试生成和播放音频
if __name__ == "__main__":
    import logging_config

    # 初始化日志配置
    logging_config.setup_logging()
    # 加载配置文件
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
        vits_speaker = vitsSpeaker(settings)

    # 要合成的日语文本
    # text = "今日はとても楽しい一日だったよ～！シアロ～(∠・ω< )⌒☆ 何か面白いことがあったら教えてね！"
    text = """
    今年の世界経済の期待に関する最新の分析は次のとおりです：\\n1. **政治的不安が世界経済に影響を与える可能性** - 特に米国前大統領トランプの可能な復帰のため、各国での政治的不安の影響は世界の繁栄に重大な影響を与えるかもしれません。[こちらから詳細情報をチェック](https://www.msn.com/en-us/money/economy/political-upheaval-around-the-world-could-spell-trouble-for-the-global-economy-in-2025/ar-AA1wyhp4)\\n2. **経済と医療における悲観的な予測** - 一部のアナリストは、医療分野の積極的な変化は難しいと考えており、業界は継続的に利益を上げ続けるが、必ずしも公共の健康を改善するわけではないとしています。[こちらから詳細情報をチェック](https://www.forbes.com/sites/joshuacohen/2025/01/01/2025-not-so-rosy-predictions-on-economy-and-healthcare/)\\n3. **ウォールストリートの2025年の期待** - 影響を及ぼす多くの要因があるとされています。人工知能革命や中国経済の減速、お金を持つべきであることに気をつけるべきです。[こちらから詳細情報をチェック](https://www.bloomberg.com/graphics/2025-investment-outlooks/)\\n4. **ビットコインの価格予測** - 2025年には、機関採用や規制の変化、マクロ経済のトレンドによってビットコインの成長が促進されるでしょう。[こちらから詳細情報をチェック](https://www.forbes.com/sites/digital-assets/2025/01/01/what-is-bitcoins-price-prediction-for-2025/)\\nこれらの情報が世界経済の最新の動向を理解するのに役立つことを願っています！"""

    # 调用合成并播放的功能
    vits_speaker.vits_play(text)
