import requests
import json


class Model:
    def __init__(self, main_settings):
        self.settings = main_settings
        self.agent_id = self.settings.get("agent_id", "agent-xxx")

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

    def get_response(self, user_input):
        """发送请求到 Letta API，并获取响应"""
        url = f"http://localhost:8283/v1/agents/{self.agent_id}/messages"
        headers = {"Content-Type": "application/json"}
        data = {"messages": [{"role": "user", "text": user_input}]}

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # 检查响应状态

            # 打印状态码和响应内容
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")

            # 确保响应是JSON格式
            if response.headers.get("Content-Type") == "application/json":
                return response.json()  # 返回响应内容
            else:
                print("响应不是JSON格式")
                return {"messages": [{"text": "返回内容格式错误"}]}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"messages": [{"text": "请求失败，请稍后重试"}]}  # 返回默认失败消息
