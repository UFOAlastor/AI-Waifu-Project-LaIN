import tkinter as tk
from ui_module import TachieDisplay
from model_module import Model

class MainApp:
    def __init__(self):
        # 初始化Tkinter窗口
        self.root = tk.Tk()

        # 初始化界面模块
        self.ui = TachieDisplay(self.root)

        # 初始化模型模块
        self.model = Model()

        # 监听用户输入
        self.ui.dialog_text.bind("<Return>", self.handle_input)

    def handle_input(self, event=None):
        """处理用户输入并与模型交互"""
        user_input = self.ui.dialog_text.get("1.0", "end-1c").strip()
        if user_input:
            response = self.model.process_input(user_input)
            self.ui.update_dialog(response)  # 更新界面显示模型响应
        return "break"

    def run(self):
        """运行应用"""
        self.ui.display()

if __name__ == "__main__":
    app = MainApp()
    app.run()
