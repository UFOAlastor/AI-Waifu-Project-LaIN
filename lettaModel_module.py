# lettaModel_module.py

import requests
import logging
from logging_config import gcww

# 获取根记录器
logger = logging.getLogger("modle_module")

from time_module import DateTime


class LettaModel:
    def __init__(self, main_settings):
        self.settings = main_settings
        self.letta_agent_id = gcww(self.settings, "letta_agent_id", "agent-xxx", logger)
        self.letta_server_ip = gcww(
            self.settings, "letta_server_ip", "localhost", logger
        )
        self.formatted_dt = DateTime()

    def get_response(self, user_name, user_input):
        """发送请求到 Letta API，并获取响应

        Args:
            user_name (str): 用户名称 (模型据此判断对话对象)
            user_input (str): 用户输入的内容

        Returns:
            json: 模型回复原始json数据
        """
        current_date_time = self.formatted_dt.get_formatted_current_datetime()
        url = f"http://{self.letta_server_ip}:8283/v1/agents/{self.letta_agent_id}/messages"
        headers = {"Content-Type": "application/json"}
        data = {
            "messages": [
                {
                    "role": "user",  # 此处不能修改, 用户输入应当固定为user
                    "text": f"[Speaker: {user_name}]\n\n\n"
                    + f"[当前时间: {current_date_time}]\n\n\n"
                    + user_input,
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # 检查响应状态

            # 打印状态码和响应内容
            logger.debug(f"响应状态码: {response.status_code}")
            logger.debug(f"响应内容: {response.text}")

            # 确保响应是JSON格式
            if response.headers.get("Content-Type") == "application/json":
                return response.json()  # 返回响应内容
            else:
                logger.debug("响应不是JSON格式")
                return {"messages": [{"text": "返回内容格式错误"}]}
        except requests.RequestException as e:
            logger.debug(f"请求失败: {e}")
            return {"messages": [{"text": "请求失败，请稍后重试"}]}  # 返回默认失败消息
