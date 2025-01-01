# main.py

import sys
from PyQt5.QtWidgets import QApplication
from ui_module import TachieDisplay  # 假设TachieDisplay在tachie_display.py中
from model_module import Model  # 假设模型相关的函数在model_module.py中


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = TachieDisplay()
        self.chat_model = Model()
        self.setup_ui()

    def setup_ui(self):
        self.window.display_text("你好，我是远山绫！有什么可以帮忙的吗？")
        self.window.dialog_text.textChanged.connect(self.on_text_change)
        self.window.show()

    def on_text_change(self):
        input_text = self.window.dialog_text.toPlainText().strip()
        if input_text:
            print(f"收到的文本: {input_text}")
            # 获取模型响应
            response = self.chat_model.get_response(input_text)
            print(f"显示文本: {response}")
            self.window.display_text(response)

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
