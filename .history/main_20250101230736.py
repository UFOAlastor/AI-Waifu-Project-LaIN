import sys, json
from PyQt5.QtWidgets import QApplication
from ui_module import TachieDisplay  # 假设TachieDisplay在tachie_display.py中
from model_module import Model  # 导入模型类


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = TachieDisplay()
        self.chat_model = Model()  # 初始化模型实例
        window = TachieDisplay()
        window.chat_model = Model()  # 确保绑定模型
        window.text_sent.connect(window.on_text_received)  # 将输入信号连接到处理方法
        self.setup_ui()

    def setup_ui(self):
        # 设置界面的一些基本内容
        self.window.display_text(
            "你好，我是远山绫！有什么可以帮忙的吗？", is_non_user_input=True
        )

        # 连接 `text_sent` 信号到 `on_text_received` 方法
        self.window.text_sent.connect(self.on_text_received)

        self.window.show()

    def on_text_received(self, input_text):
        # 当 `send_text` 发射信号时，这个方法会被调用
        print(f"收到的文本: {input_text}")

        # 获取模型的回复并显示
        if input_text:
            try:
                response = self.chat_model.get_response(input_text)

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
                    # 从 'arguments' 中提取 'message'
                    reply_text = tool_call_message.get("tool_call", {}).get(
                        "arguments", ""
                    )
                    # 解析 'arguments' 字符串以提取实际消息
                    try:
                        # 'arguments' 是一个JSON字符串，需要加载它
                        parsed_arguments = json.loads(reply_text)
                        final_message = parsed_arguments.get("message", "没有消息内容")
                    except json.JSONDecodeError:
                        final_message = "无法解析消息"
                else:
                    final_message = "没有有效的回复"

                # 显示回复
                self.window.display_text(final_message, is_non_user_input=True)
            except Exception as e:
                print(f"Error: {e}")
                self.window.display_text(
                    "对不起，发生了错误。请稍后再试。", is_non_user_input=True
                )

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
