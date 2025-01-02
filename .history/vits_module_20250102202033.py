import requests
import pydub
from io import BytesIO
import time
import pygame  # 用于播放音频
import threading  # 导入线程模块


class vitsSpeaker:
    # 静态变量，用于保存配置
    API_URL = "http://127.0.0.1:23456/voice/vits"
    SPEAKER_ID = 4

    @staticmethod
    def get_audio_stream(text, speaker_id=None, lang="zh", format="wav", length=1.0):
        """发送请求并获取音频流"""
        speaker_id = (
            speaker_id or vitsSpeaker.SPEAKER_ID
        )  # 如果未传入speaker_id，使用默认的SPEAKER_ID
        params = {
            "text": text,
            "id": speaker_id,
            "lang": lang,
            "format": format,
            "length": length,
        }

        try:
            response = requests.get(vitsSpeaker.API_URL, params=params, stream=True)

            # 判断请求是否成功
            if response.status_code == 200:
                return response.content
            else:
                print(f"音频请求失败，状态码: {response.status_code}")
                return None

        except requests.RequestException as e:
            print(f"请求发生错误: {e}")
            return None

    @staticmethod
    def play_audio(audio_data):
        """播放音频"""
        try:
            audio = pydub.AudioSegment.from_wav(BytesIO(audio_data))
            pygame.mixer.init(frequency=audio.frame_rate)  # 初始化pygame的音频播放
            pygame.mixer.music.load(BytesIO(audio_data))  # 加载音频数据
            pygame.mixer.music.play()  # 播放音频

            # 等待音频播放完成
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            print(f"播放音频发生错误: {e}")

    @staticmethod
    def vits_play(text, speaker_id=None, lang="zh", format="wav", length=1.0):
        """输入文本，生成并播放音频"""
        try:
            audio_data = vitsSpeaker.get_audio_stream(
                text, speaker_id, lang, format, length
            )

            if audio_data is None:
                print("生成音频失败，无法播放。")
                return

            print("音频生成成功，正在播放...")

            # 创建一个新的线程来播放音频，这样主程序就不会被阻塞
            audio_thread = threading.Thread(
                target=vitsSpeaker.play_audio, args=(audio_data,)
            )
            audio_thread.start()

            # 继续执行其他任务
            print("主程序继续执行，音频正在播放...")

        except Exception as e:
            print(f"发生错误: {e}")


# 测试生成和播放音频
if __name__ == "__main__":
    # 加载配置文件
    vitsSpeaker.load_settings("./config.json")

    # 要合成的日语文本
    text = "今日はとても楽しい一日だったよ～！シアロ～(∠・ω< )⌒☆ 何か面白いことがあったら教えてね！"

    # 调用合成并播放的功能
    vitsSpeaker.vits_play(text)
