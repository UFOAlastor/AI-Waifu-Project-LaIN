import requests
import pydub
from io import BytesIO
import time
import pygame  # 用于播放音频
import json


class VITSModule:
    def __init__(self, config_path="./config.json"):
        # 加载配置文件
        settings = self.load_settings(config_path)

        # 设置默认值
        self.API_URL = settings.get("vits_api_url", "http://127.0.0.1:23456/voice/vits")
        self.SPEAKER_ID = settings.get("SPEAKER_ID", 4)

    # 函数: 发送请求并获取音频流
    def get_audio_stream(
        self, text, speaker_id=None, lang="zh", format="wav", length=1.0
    ):
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

        response = requests.get(self.API_URL, params=params, stream=True)

        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Failed to get audio: {response.status_code}")

    # 函数: 播放音频
    def play_audio(self, audio_data):
        audio = pydub.AudioSegment.from_wav(BytesIO(audio_data))
        pygame.mixer.init(frequency=audio.frame_rate)  # 初始化pygame的音频播放
        pygame.mixer.music.load(BytesIO(audio_data))  # 加载音频数据
        pygame.mixer.music.play()  # 播放音频

        # 等待音频播放完成
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    # 函数: 加载配置文件
    def load_settings(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"未找到设置文件: {file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"设置文件格式错误: {file_path}")
            return {}


# 测试生成和播放音频
if __name__ == "__main__":
    # 初始化VITS模块
    vits_module = VITSModule()

    # 要合成的日语文本
    text = "今日はとても楽しい一日だったよ～！シアロ～(∠・ω< )⌒☆ 何か面白いことがあったら教えてね！"

    try:
        audio_data = vits_module.get_audio_stream(text)
        print("音频生成中...")
        vits_module.play_audio(audio_data)
        print("播放完成！")
    except Exception as e:
        print(f"发生错误: {e}")
