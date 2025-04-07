# functioncall_module.py

import ollama
import yaml, json, uuid
import logging
from logging_config import gcww

# 获取根记录器
logger = logging.getLogger("functioncall_module")

# 导入模块类
from ollamaModel_module import ollamaModel  # ollama框架
from openaiTypeModel_module import openaiTypeModel  # openaiType模型

# 导入function
from functioncall import load_custom_functions


class FunctioncallManager:
    def __init__(self, main_settings):
        """初始化FunctioncallManager类"""

        # 获取模型框架类型
        self.model_frame_type = gcww(
            main_settings, "model_frame_type", "openaiType", logger
        )

        # 初始化模型实例
        if self.model_frame_type == "ollama":
            self.chat_model = ollamaModel(main_settings)
        elif self.model_frame_type == "openaiType":
            self.chat_model = openaiTypeModel(main_settings)
        else:
            raise ValueError(
                f"FunctionCall模块不支持的模型框架类型: {self.model_frame_type}"
            )

        # 初始化函数映射
        self.functions = []
        self.function_map = {}

        # 加载自定义函数描述和实现
        func_descriptions, func_implementations = load_custom_functions()
        self.register_func_desc(func_descriptions)
        self.register_func_impl(func_implementations)

    def register_func_desc(self, func_desc):
        if isinstance(func_desc, list):
            self.functions += func_desc
        else:
            self.functions.append(func_desc)

    def register_func_impl(self, name, func_impl=None):
        """
        支持三种调用方式：
        1. 注册单个函数：register_function("func_name", func_impl)
        2. 批量注册字典：register_function({"func1": func1, "func2": func2})
        3. 批量注册列表：register_function([("func1", func1), ("func2", func2)])
        """
        if isinstance(name, dict) and func_impl is None:
            self.function_map.update(name)
        elif isinstance(name, (list, tuple)) and func_impl is None:
            for n, f in name:
                self.function_map[n] = f
        elif isinstance(name, str) and func_impl is not None:
            self.function_map[name] = func_impl
        else:
            raise TypeError("支持格式：1) (str, func) 2) {str:func} 3) [(str,func)]")

    def show_registered_functions(self):
        for func_name, _ in self.function_map.items():
            logger.debug(f"加载函数: {func_name}")

    def get_response(self, user_name: str, user_input: str) -> str:
        # 先发送用户消息给LLM
        self.chat_model.add_message("user", user_name, user_input)

        if self.model_frame_type == "openaiType":
            response = self.chat_model.client.chat.completions.create(
                model=self.chat_model.model,
                messages=self.chat_model.messages,
                functions=self.functions,
                function_call="auto",
                stream=False,
            )
            message = response.choices[0].message

            if message.function_call:
                # 如果LLM进行函数调用，执行相应的函数
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)

                if function_name in self.function_map:
                    # 执行函数调用
                    logger.debug(
                        f"FunctionCall模块执行函数调用: {function_name}: {function_args}"
                    )
                    function_response = self.function_map[function_name](
                        **function_args
                    )
                    self.chat_model.messages.append(
                        {
                            "role": "assistant",
                            "content": "",
                            "function_call": {
                                "name": function_name,
                                "arguments": message.function_call.arguments,
                            },
                        }
                    )
                    self.chat_model.messages.append(
                        {
                            "role": "function",
                            "name": function_name,
                            "content": str(function_response),
                        }
                    )
                    second_response = self.chat_model.client.chat.completions.create(
                        model=self.chat_model.model,
                        messages=self.chat_model.messages,
                        stream=False,
                    )
                    final_response = second_response.choices[0].message.content
                    self.chat_model.add_message(
                        "assistant", self.chat_model.bot_name, final_response
                    )
                    return final_response
            else:
                response_content = message.content

        elif self.model_frame_type == "ollama":
            _tools = []
            for _func in self.functions:
                _tools.append(
                    {
                        "type": "function",
                        "function": _func,
                    }
                )

            try:
                response = ollama.chat(
                    model=self.chat_model.model,
                    messages=self.chat_model.messages,
                    options={
                        "temperature": self.chat_model.temperature,
                        "max_tokens": self.chat_model.max_tokens,
                    },
                    tools=_tools,
                )
                message = response.get("message", {})
                logger.debug(f"response: {message}")
            except Exception as e:
                return f"API请求错误: {str(e)}"

            if "tool_calls" in message:
                for tool_call in message["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    function_args = tool_call["function"]["arguments"]
                    print(f"函数名称: {function_name}")
                    print(f"参数: {function_args}")

                    if function_name in self.function_map:
                        # 执行函数调用
                        logger.debug(
                            f"FunctionCall模块执行函数调用: {function_name}: {function_args}"
                        )
                        function_response = self.function_map[function_name](
                            **function_args
                        )
                        # 生成唯一调用ID
                        call_id = str(uuid.uuid4())
                        # 助手消息
                        self.chat_model.messages.append(
                            {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": call_id,
                                        "type": "function",
                                        "function": {
                                            "name": function_name,
                                            "arguments": function_args,
                                        },
                                    }
                                ],
                            }
                        )
                        # 工具响应消息
                        self.chat_model.messages.append(
                            {
                                "role": "tool",
                                "content": json.dumps(
                                    {
                                        "status": "success",
                                        "data": function_response,
                                    },
                                    ensure_ascii=False,
                                ),
                                "tool_call_id": call_id,
                            }
                        )

                second_response = ollama.chat(
                    model=self.chat_model.model,
                    messages=self.chat_model.messages,
                    options={
                        "temperature": self.chat_model.temperature,
                        "max_tokens": self.chat_model.max_tokens,
                    },
                )
                final_response = second_response.get("message", {}).get("content", "")
                self.chat_model.add_message(
                    "assistant", self.chat_model.bot_name, final_response
                )
                return final_response
            else:
                response_content = message.get("content", "")

        self.chat_model.add_message(
            "assistant", self.chat_model.bot_name, response_content
        )
        return response_content


if __name__ == "__main__":
    import yaml
    import logging_config

    # 初始化日志配置
    logging_config.setup_logging()

    """加载配置文件"""
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    chat_model = FunctioncallManager(settings)

    while True:
        try:
            user_input = input("用户: ")
            if user_input.lower() == "exit":
                break
            logger.debug(f"AI助手: {chat_model.get_response('Unknown', user_input)}")
        except KeyboardInterrupt:
            break

    logger.debug("对话已结束")
