# functioncall_module.py

import yaml
import json
from typing import Dict, Any, List
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
    def __init__(
        self,
        main_settings,
        func_descriptions: List[Dict[str, Any]],
        func_implementations: Dict,
    ):
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
        self.functions = func_descriptions
        self.function_map = self.register_function(func_implementations)

        for func_name, _ in func_implementations.items():
            logger.debug(f"加载函数: {func_name}")

    def register_function(self, name, func=None):
        """
        支持三种调用方式：
        1. 注册单个函数：register_function("func_name", func_impl)
        2. 批量注册字典：register_function({"func1": func1, "func2": func2})
        3. 批量注册列表：register_function([("func1", func1), ("func2", func2)])
        """
        _function_map = {}
        if isinstance(name, dict) and func is None:
            _function_map.update(name)
        elif isinstance(name, (list, tuple)) and func is None:
            for n, f in name:
                _function_map[n] = f
        elif isinstance(name, str) and func is not None:
            _function_map[name] = func
        else:
            raise TypeError("支持格式：1) (str, func) 2) {str:func} 3) [(str,func)]")

        return _function_map

    def get_response(self, user_name: str, user_input: str) -> str:
        # 先发送用户消息给LLM
        self.chat_model.add_message("user", user_name, user_input)

        response = self.chat_model.client.chat.completions.create(
            model=self.chat_model.model,
            messages=self.chat_model.messages,
            functions=self.functions,
            function_call="auto",
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

                function_response = self.function_map[function_name](**function_args)

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
                    model=self.chat_model.model, messages=self.chat_model.messages
                )

                final_response = second_response.choices[0].message.content
                self.chat_model.add_message(
                    "assistant", self.chat_model.bot_name, final_response
                )
                return final_response

        response_content = message.content
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

    func_descriptions, func_implementations = load_custom_functions()
    chat_model = FunctioncallManager(settings, func_descriptions, func_implementations)

    while True:
        try:
            user_input = input("用户: ")
            if user_input.lower() == "exit":
                break
            logger.debug(f"AI助手: {chat_model.get_response('Unknown', user_input)}")
        except KeyboardInterrupt:
            break

    logger.debug("对话已结束")
