# model_module.py
import requests

agent_id = "agent-xxxxxxx"

class Model:
    @staticmethod
    def get_response(agent_id, user_input):
        url = f'http://localhost:8283/v1/agents/{agent_id}/messages'
        headers = {'Content-Type': 'application/json'}
        message = Model.get_response(user_input)
        data = {
            "messages": [
                {
                    "role": "user",
                    "text": user_input
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        return response.json()

