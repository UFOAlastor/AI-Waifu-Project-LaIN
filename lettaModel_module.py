# lettaModel_module.py

import requests, yaml
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

                if "error" in response:
                    self.window.display_text(
                        "对不起，发生了错误。请稍后再试。", is_non_user_input=True
                    )
                    return

                # 查找第一个包含 'tool_call_message' 且 name = 'send_message' 类型的消息
                tool_call_message = next(
                    (
                        msg
                        for msg in response.get("messages", [])
                        if msg.get("message_type") == "tool_call_message"
                        and msg.get("tool_call", {}).get("name") == "send_message"
                    ),
                    None,
                )

                if tool_call_message:
                    reply_text = tool_call_message.get("tool_call", {}).get(
                        "arguments", ""
                    )
                    try:
                        parsed_arguments = yaml.safe_load(reply_text)
                        return str(
                            parsed_arguments.get("message", "没有消息内容")
                        )  # 返回响应内容
                    except yaml.YAMLError as e:
                        return "没有有效的回复"
                else:
                    return "没有有效的回复"
            else:
                logger.debug("响应不是JSON格式")
                return "没有有效的回复"
        except requests.RequestException as e:
            logger.debug(f"请求失败: {e}")
            return "没有有效的回复"  # 返回默认失败消息
