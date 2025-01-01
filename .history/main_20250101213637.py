# main.py

import sys
from PyQt5.QtWidgets import QApplication
from ui_module import TachieDisplay  # 假设TachieDisplay在tachie_display.py中
from model_module import Model  # 假设模型相关的函数在model_module.py中


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = TachieDisplay()
        self.chat_model = Model()  # 初始化对话模型
        self.setup_ui()

    def setup_ui(self):
        # 设置界面的一些基本内容
        self.window.display_text("你好，我是远山绫！有什么可以帮忙的吗？", is_non_user_input=True)

        # 连接 `text_sent` 信号到 `on_text_received` 方法
        self.window.text_sent.connect(self.on_text_received)

        self.window.show()

    def on_text_received(self, input_text):
        # 当 `send_text` 发射信号时，这个方法会被调用
        print(f"收到的文本: {input_text}")

        # 获取模型的回复
        if input_text:
            try:
                response = self.chat_model.get_response(input_text)
                # 显示模型的回复
                self.window.display_text(response, is_non_user_input=True)
            except Exception as e:
                print(f"Error: {e}")
                self.window.display_text("对不起，发生了错误。请稍后再试。", is_non_user_input=True)

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
