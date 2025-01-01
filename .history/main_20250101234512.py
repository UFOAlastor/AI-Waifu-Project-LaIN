import re
import sys
import json
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication
from ui_module import TachieDisplay  # 假设TachieDisplay在tachie_display.py中
from model_module import Model  # 导入模型类


class ChatModelWorker(QThread):
    """用于后台运行模型的线程"""
    response_ready = pyqtSignal(dict)

    def __init__(self, model, input_text):
        super().__init__()
        self.model = model
        self.input_text = input_text

    def run(self):
        try:
            response = self.model.get_response(self.input_text)
            self.response_ready.emit(response)
        except Exception as e:
            print(f"Error in model worker: {e}")
            self.response_ready.emit({"error": str(e)})


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = TachieDisplay()
        self.chat_model = Model()  # 初始化模型实例
        self.setup_ui()
        self.typing_animation_timer = QTimer()
        self.typing_dots = ""

    def setup_ui(self):
        self.window.display_text(
            "你好，我是远山绫！有什么可以帮忙的吗？", is_non_user_input=True
        )
        self.window.text_sent.connect(self.on_text_received)
        self.window.show()

    def on_text_received(self, input_text):
        if input_text:
            # 显示动态省略号动画
            self.start_typing_animation()

            # 启动后台线程调用模型
            self.worker = ChatModelWorker(self.chat_model, input_text)
            self.worker.response_ready.connect(self.on_model_response)
            self.worker.start()

    def start_typing_animation(self):
        """启动动态省略号动画"""
        self.typing_dots = ""
        self.window.display_text("绫正在思考中", is_non_user_input=True)
        self.typing_animation_timer.timeout.connect(self.update_typing_animation)
        self.typing_animation_timer.start(4000)  # 每隔 4000ms 更新一次

    def update_typing_animation(self):
        """更新动态省略号"""
        if len(self.typing_dots) < 3:
            self.typing_dots += "。"
        else:
            self.typing_dots = ""
        self.window.display_text(f"绫正在思考中{self.typing_dots}", is_non_user_input=True)

    def stop_typing_animation(self):
        """停止动态省略号动画"""
        self.typing_animation_timer.stop()
        self.typing_animation_timer.timeout.disconnect(self.update_typing_animation)

    def on_model_response(self, response):
        """处理模型的回复"""
        # 停止动态省略号动画
        self.stop_typing_animation()

        if "error" in response:
            self.window.display_text("对不起，发生了错误。请稍后再试。", is_non_user_input=True)
            return

        # 查找第一个包含 'tool_call_message' 类型的消息
        tool_call_message = next(
            (
                msg
                for msg in response.get("messages", [])
                if msg.get("message_type") == "tool_call_message"
            ),
            None,
        )

        if tool_call_message:
            reply_text = tool_call_message.get("tool_call", {}).get("arguments", "")
            try:
                parsed_arguments = json.loads(reply_text)
                final_message = parsed_arguments.get("message", "没有消息内容")
            except json.JSONDecodeError:
                final_message = "无法解析消息"
        else:
            final_message = "没有有效的回复"

        # 显示最终的回复
        self.window.display_text(final_message, is_non_user_input=True)

    def parse_bot_reply(reply: str, delimiter: str = "|||"):
        """
        解析 {表情}|||{中文}|||{日语} 格式的字符串，确保对分隔符冲突的处理安全。
        :param reply: 输入的字符串，格式如 {表情}|||{中文}|||{日语}
        :param delimiter: 自定义分隔符，默认为 "|||"
        :return: 一个包含 表情, 中文, 日语 的字典
        """
        # 将分隔符进行正则转义，确保匹配时安全
        escaped_delimiter = re.escape(delimiter)

        # 使用正则表达式确保划分三部分
        pattern = rf"^(.*?)\s*{escaped_delimiter}\s*(.*?)\s*{escaped_delimiter}\s*(.*?)$"
        match = re.match(pattern, reply)

        if not match:
            raise ValueError(
                f"输入字符串格式不正确，应为 {{表情}}{delimiter}{{中文}}{delimiter}{{日语}}"
            )

        # 提取三部分内容
        expression, chinese, japanese = match.groups()

        return {
            "表情": expression.strip(),
            "中文": chinese.strip(),
            "日语": japanese.strip(),
        }

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
