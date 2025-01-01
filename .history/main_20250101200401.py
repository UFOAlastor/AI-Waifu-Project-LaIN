# main.py
import tkinter as tk
from ui_module import TachieDisplay  # 假设TachieDisplay在tachie_display.py中
from model_module import generate_text  # 假设模型相关的函数在model_module.py中

class Application:
    def __init__(self, root):
        self.root = root
        self.app = TachieDisplay(self.root)  # 初始化TachieDisplay

        # 设置示例输入
        self.input_data = "请告诉我一些故事"

        # 生成文本
        generated_text = generate_text(self.input_data)

        # 将生成的文本显示到TachieDisplay的对话框中
        self.app.display_text(generated_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()
