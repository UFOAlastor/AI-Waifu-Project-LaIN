# lettaModel_module.py

import requests, yaml
import logging
from logging_config import gcww

# 获取根记录器
logger = logging.getLogger("lettaModle_module")

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
            response.raise_for_status()

            logger.debug(f"响应状态码: {response.status_code}")
            logger.debug(f"响应内容: {response.text}")

            if response.status_code != 200:
                return f"请求异常, status code: {response.status_code}"

            if response.headers.get("Content-Type") == "application/json":
                response_data = response.json()  # 解析JSON响应

                # 在messages数组中查找assistant_message
                assistant_message = next(
                    (
                        msg
                        for msg in response_data.get("messages", [])
                        if msg.get("message_type") == "assistant_message"
                    ),
                    None,
                )

                if assistant_message:  # 直接获取assistant_message字段
                    return assistant_message.get("assistant_message", "没有消息内容")
                return "没有有效的回复"
            else:
                logger.debug("响应不是JSON格式")
                return "响应不是JSON格式"
        except requests.RequestException as e:
            logger.debug(f"请求失败: {e}")
            return f"请求失败: {e}"


if __name__ == "__main__":
    import yaml
    import logging_config

    # 初始化日志配置
    logging_config.setup_logging()

    """加载配置文件"""
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    chatbot = LettaModel(settings)

    while True:  # 非流式生成测试
        try:
            user_input = input("用户: ")
            if user_input.lower() == "exit":
                break

            print("AI助手: ", end="", flush=True)
            print(chatbot.get_response("Unknown", user_input), flush=True)

        except KeyboardInterrupt:
            break
