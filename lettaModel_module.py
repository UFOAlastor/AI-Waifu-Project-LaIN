# lettaModel_module.py

from letta_client import Letta
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
        # 创建letta client对象 (测试还不支持https)
        self.client = Letta(base_url="http://" + self.letta_server_ip + ":8283")
        # 创建时间日期格式化工具对象
        self.formatted_dt = DateTime()

    def get_response(self, user_name, user_input):
        """发送请求到 Letta API，并获取响应

        Args:
            user_name (str): 用户名称 (模型据此判断对话对象)
            user_input (str): 用户输入的内容

        Returns:
            str: 模型回复内容
        """
        current_date_time = self.formatted_dt.get_formatted_current_datetime()

        response = self.client.agents.messages.create(
            agent_id=self.letta_agent_id,
            messages=[
                {
                    "role": "user",  # 此处不能修改, 用户输入应当固定为user
                    "content": f"[Speaker: {user_name}]\n\n"
                    + f"[当前时间: {current_date_time}]\n\n"
                    + user_input,
                }
            ],
        )

        logger.debug(f"模型回复: {response}")

        for msg in response.messages:
            if msg.message_type == "assistant_message":
                return msg.content

        return "没有有效回复"


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
