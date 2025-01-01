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

        # 监听回车事件
        self.window.dialog_text.returnPressed.connect(self.on_enter_pressed)

        self.window.show()

    def on_enter_pressed(self):
        # 获取输入的文本
        input_text = self.window.dialog_text.toPlainText().strip()
        if input_text:
            # 获取模型的回复
            try:
                response = self.chat_model.get_response(input_text)
                # 显示模型的回复
                self.window.display_text(response)
                # 清空输入框
                self.window.dialog_text.clear()
            except Exception as e:
                print(f"Error: {e}")  # 这里可以替换为更优雅的错误处理
                self.window.display_text("对不起，发生了错误。请稍后再试。")
                self.window.dialog_text.clear()

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
