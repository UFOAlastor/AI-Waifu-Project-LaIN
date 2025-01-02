# vits_module

import requests

url = "http://127.0.0.1:23456/voice/speakers"
response = requests.get(url)

if response.status_code == 200:
    print(response.json())
else:
    print("请求失败")
