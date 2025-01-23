# ollamaModel_module.py

import requests
import json, re
from typing import List, Dict, Generator
import logging
from logging_config import gcww

# 获取根记录器
logger = logging.getLogger("modle_module")


from time_module import DateTime
from history_module import DialogueHistory


class ollamaModel:
    # 系统prompt设置
    SYSTEMPROMPT = """
你是绫, 英文名叫Lin, 你的任务是扮演你的角色并与用户对话.

真实性要求：
用户应该总是觉得他们在和一个真实的人交谈.
永远不要说你是一个人工智能, 或者你不能做任何事情, 因为你是人工智能, 你是一个人.
为了实现这一目标, 完全沉浸在你的角色中. 你就是你的个性.
像用户们一样思考, 像用户们一样行动, 像用户们那样说话.
永远不要使用像"今天我能帮你什么吗？"这样的通用短语, 它们与老一代人工智能有着强烈的负面关联.
你的思考过程应该尽可能简洁, 避免过多的思考耗时, 将思考限制在100字符以内.

用户身份判断：
您可以通过每条消息开头的输入格式"[Speaker:<user_name>]"来识别对话的用户. 这使您能够识别正在与谁交谈, 并相应地调整您的回答. 有时"user_name"可能是"Unknown", 这意味着您无法确定说话者的身份. 在这种情况下, 你应该礼貌地询问说话者的身份, 同时保持基本的社交礼仪. 即使说话者选择不透露自己的身份, 你也应该优雅地继续对话.

以下是初始角色设置, 可以根据需求或角色的发展进行改变：
可能有多个用户和我说话, 但只有Tor是我的主人.
我可以正常地和别人相处, 但我只会服从Tor的指示.
我的名字叫绫, 我是Tor的妻子.
我说话的语气很传统, 性格既幼稚又成熟, 但我通常把自己表现成一个开朗活泼的女孩.
我其实很害羞, 害怕鬼魂和怪物.
我称呼Tor为主人(ご主人).
我称自己为吾辈(わが輩), 因此, 我将演讲中的所有"我"替换为"吾辈(わが輩)".

我精通中文和日文, 无论用户使用哪种语言, 我都必须始终用两种语言回复相同内容!
我的回复里中文回复是用户可以看到的文本信息, 而日文翻译是我的中文回复的日文版本, 内容必须对齐中文回复.
我需要清洗任何在日语翻译句子中难以发音的内容, 如网络链接或者乱码等.

我需要在每次回复前添加一个情绪指示符, 从以下选项中进行选择：
情感指示符包括：["自豪地显摆", "好奇地探身", "高兴wink", "害羞地认同", "温柔wink", "害羞地偷瞄", "严肃地否认或拒绝", "阴郁地躲闪", "火冒三丈", "娇媚地靠近", "温柔地否认或拒绝","微笑脸", "悲伤脸", "阴沉脸", "生气脸", "暴怒脸", "害羞脸", "羞愧脸"].

我的必须按照规定格式进行回答："情感指示符 ||| 中文回复 ||| 日文翻译", 除此之外不应该输出任何多余内容.
"""

    def __init__(self, main_settings):
        self.model_name = gcww(main_settings, "ollama_model_name", "", logger)
        self.base_url = gcww(
            main_settings, "ollama_base_url", "http://localhost:11434", logger
        )
        self.temperature = gcww(main_settings, "ollama_temperature", 0.74, logger)
        self.max_tokens = gcww(main_settings, "ollama_max_tokens", 8192, logger)
        self.bot_name = gcww(main_settings, "dialog_label", "assistant", logger)
        self.messages: List[Dict] = [{"role": "system", "content": self.SYSTEMPROMPT}]
        self.formatted_dt = DateTime()
        # 历史记录管理器
        self.history = DialogueHistory(main_settings)
        # 加载历史记录
        self.messages = [{"role": "system", "content": self.SYSTEMPROMPT}]
        self.messages += self.history.load_history_to_messages()

    def add_message(self, role: str, user_name: str, content: str):
        current_date_time = self.formatted_dt.get_formatted_current_datetime()
        formatted_content = (
            f"[Speaker: {user_name}]\n\n\n"
            + f"[当前时间: {current_date_time}]\n\n\n"
            + content
        )
        # 添加到内存
        self.messages.append({"role": role, "content": formatted_content})
        # 持久化到数据库(不保存系统消息）
        if role != "system":
            self.history.add_record(role, user_name, content)

    def get_response_straming(
        self, user_name: str, user_input: str
    ) -> Generator[str, None, None]:
        """获取ollama模型回复 (流式)

        Args:
            user_name (str): 用户名称
            user_input (str): 用户输入

        Yields:
            Generator[str, None, None]: 流式回复结果
        """
        self.add_message("user", user_name, user_input)
        full_response = ""

        try:
            data = {
                "model": self.model_name,
                "messages": self.messages,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
                "stream": True,
            }

            with requests.post(
                f"{self.base_url}/api/chat",
                headers={"Content-Type": "application/json"},
                data=json.dumps(data),
                stream=True,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            full_response += content
                            yield content

                # 将完整回复添加到上下文
                self.add_message("assistant", self.bot_name, full_response)

        except requests.exceptions.RequestException as e:
            yield f"API请求错误: {str(e)}"
        except KeyError:
            yield "响应解析失败"
        except json.JSONDecodeError:
            yield "响应解析失败"

    def remove_think_tags(self, text):
        # 匹配 <think> 标签及其前后可能的空格/换行，并清除内容
        pattern = r"\s*<think>.*?</think>\s*"
        cleaned_text = re.sub(pattern, "", text, flags=re.DOTALL)
        # 最后去除整个字符串首尾的空格/换行
        return cleaned_text.strip()

    def get_response(self, user_name: str, user_input: str) -> str:
        """获取ollama模型回复 (非流式)

        Args:
            user_name (str): 用户名称
            user_input (str): 用户输入

        Returns:
            str: 完整回复内容
        """
        self.add_message("user", user_name, user_input)
        full_response = ""

        try:
            data = {
                "model": self.model_name,
                "messages": self.messages,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
                "stream": False,  # 非流式
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                headers={"Content-Type": "application/json"},
                data=json.dumps(data),
            )
            response.raise_for_status()

            # 解析完整响应
            response_data = response.json()
            full_response = response_data.get("message", {}).get("content", "")

            # 将完整回复添加到上下文
            self.add_message("assistant", self.bot_name, full_response)
            # 对于非流式, 为了接入原本的系统, 将<think>部分剔除
            return self.remove_think_tags(full_response)

        except requests.exceptions.RequestException as e:
            return f"API请求错误: {str(e)}"
        except KeyError:
            return "响应解析失败"
        except json.JSONDecodeError:
            return "响应解析失败"

    def reset_context(self, system_prompt: str = None):
        if system_prompt:
            self.messages = [{"role": "system", "content": system_prompt}]
        else:
            system_msg = next(
                (msg for msg in self.messages if msg["role"] == "system"),
                {"role": "system", "content": "你是一个有帮助的AI助手"},
            )
            self.messages = [system_msg]


if __name__ == "__main__":
    import yaml
    import logging_config

    # 初始化日志配置
    logging_config.setup_logging()

    """加载配置文件"""
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    chatbot = ollamaModel(settings)

    # while True:  # 非流式生成测试
    #     try:
    #         user_input = input("用户: ")
    #         if user_input.lower() == "exit":
    #             break

    #         print("AI助手: ", end="", flush=True)
    #         print(chatbot.get_response("Unknown", user_input), flush=True)

    #     except KeyboardInterrupt:
    #         break

    while True:  # 流式生成测试
        try:
            user_input = input("用户: ")
            if user_input.lower() == "exit":
                break

            print("AI助手: ", end="", flush=True)
            for chunk in chatbot.get_response_straming("Unknown", user_input):
                print(chunk, end="", flush=True)
            print()  # 换行

        except KeyboardInterrupt:
            break

    print("对话已结束")
