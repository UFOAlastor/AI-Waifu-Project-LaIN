# main.py
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import tkinter as tk
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
        self.window.display_text("你好，我是远山绫！有什么可以帮忙的吗？")

        # 假设与模型交互是通过发送用户输入并获得回复
        self.window.dialog_text.textChanged.connect(self.on_text_change)

        self.window.show()

    def on_text_change(self):
        # 当用户输入文本时，调用模型进行回复
        input_text = self.window.dialog_text.toPlainText().strip()
        if input_text:
            # 获取模型的回复
            response = self.chat_model.get_response(input_text)
            # 显示模型的回复
            self.window.display_text(response)

    def run(self):
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()

