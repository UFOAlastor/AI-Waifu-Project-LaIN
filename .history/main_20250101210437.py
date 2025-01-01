# main.py
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from ui_module import TachieDisplay  # 假设TachieDisplay在tachie_display.py中
from model_module import Model  # 假设模型相关的函数在model_module.py中


class MainApp:
    def __init__(self):
        self.window = TachieDisplay()  # 初始化 TachieDisplay 窗口
        self.setup_ui()

    def setup_ui(self):
        self.window.show()  # 显示 TachieDisplay 窗口
        # 事件过滤器应该安装在 TachieDisplay 的对象上，而不是 MainApp
        self.window.dialog_text.installEventFilter(self.window)  # 安装事件过滤器

    def on_text_change(self):
        input_text = self.window.dialog_text.toPlainText().strip()
        if input_text:
            # 检测回车键是否按下
            if self.window.dialog_text.hasFocus() and "\n" in input_text:
                self.handle_input(input_text)
                self.window.dialog_text.clear()  # 清空文本框
                return True  # 阻止默认回车换行行为
        return False

    def handle_input(self, input_text):
        # 获取模型的回复
        response = self.chat_model.get_response(input_text)
        # 显示模型的回复
        self.window.display_text(response)

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
