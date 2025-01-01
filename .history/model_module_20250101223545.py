# model_module.py
import requests

class Model:
    def __init__(self):
        self.settings = self.load_settings("./config.json")
        self.agent_id = self.settings.get("agent_id", "agent-xxx")

    def get_response(user_input):
        url = f'http://localhost:8283/v1/agents/{self.agent_id}/messages'
        headers = {'Content-Type': 'application/json'}
        data = {
            "messages": [
                {
                    "role": "user",
                    "text": user_input
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        print("返回值:", response)
        return response.json()

