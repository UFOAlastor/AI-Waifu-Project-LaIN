# vits_module

import requests
import pydub
from io import BytesIO
import time
import pygame  # 用于播放音频

# VITS API地址
API_URL = "http://127.0.0.1:23456/voice/vits"
SPEAKER_ID = 4  # 这里填入你所需的角色ID


# 函数: 发送请求并获取音频流
def get_audio_stream(text, speaker_id=SPEAKER_ID, lang="zh", format="wav", length=1.0):
    params = {
        "text": text,
        "id": speaker_id,
        "lang": lang,
        "format": format,
        "length": length,
    }

    response = requests.get(API_URL, params=params, stream=True)

    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to get audio: {response.status_code}")


# 函数: 播放音频
def play_audio(audio_data):
    audio = pydub.AudioSegment.from_wav(BytesIO(audio_data))
    pygame.mixer.init(frequency=audio.frame_rate)  # 初始化pygame的音频播放
    pygame.mixer.music.load(BytesIO(audio_data))  # 加载音频数据
    pygame.mixer.music.play()  # 播放音频

    # 等待音频播放完成
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


# 测试生成和播放音频
if __name__ == "__main__":
    text = "今日はとても楽しい一日だったよ～！シアロ～(∠・ω< )⌒☆ 何か面白いことがあったら教えてね！"

    try:
        audio_data = get_audio_stream(text)
        print("音频生成中...")
        play_audio(audio_data)
        print("播放完成！")
    except Exception as e:
        print(f"发生错误: {e}")
