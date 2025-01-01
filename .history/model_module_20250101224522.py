import requests
import json


class Model:
    def __init__(self, config_path="./config.json"):
        self.settings = self.load_settings(config_path)
        self.agent_id = self.settings.get("agent_id", "agent-xxx")

    def load_settings(self, config_path):
        """从配置文件加载设置"""
        try:
            with open(config_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print("配置文件未找到！")
            return {}
        except json.JSONDecodeError:
            print("配置文件格式错误！")
            return {}

    def get_response(self, user_input):
        """发送请求到 Letta API，并获取响应"""
        url = f"http://localhost:8283/v1/agents/{self.agent_id}/messages"
        headers = {"Content-Type": "application/json"}
        data = {"messages": [{"role": "user", "text": user_input}]}

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # 检查响应状态
            print(response.json())
            return response.json()  # 返回响应内容
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"messages": [{"text": "请求失败，请稍后重试"}]}  # 返回默认失败消息
