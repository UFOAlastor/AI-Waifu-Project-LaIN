# vits_module

import requests

url = "http://127.0.0.1:23456/voice/speakers"
response = requests.get(url)

if response.status_code == 200:
    print(response.json())
else:
    print("请求失败")

url = "http://127.0.0.1:23456/voice/vits?text=Hello&id=142&format=wav&lang=zh&length=1.4"
response = requests.get(url)

if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
else:
    print("语音生成失败")
