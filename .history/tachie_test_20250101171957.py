import tkinter as tk
from PIL import Image, ImageTk

class CharacterDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("动漫人物立绘展示")

        # 创建一个标签来显示图片
        self.image_label = tk.Label(root)
        self.image_label.pack()

        # 加载初始表情图片
        self.load_image("./tachie/Murasame/正常.png")

        # 按钮切换图片
        self.switch_button = tk.Button(root, text="切换表情", command=self.switch_expression)
        self.switch_button.pack()

    def load_image(self, image_path):
        """加载并显示图片"""
        image = Image.open(image_path)
        photo = ImageTk.PhotoImage(image)
        self.image_label.config(image=photo)
        self.image_label.image = photo  # 保持对图片的引用

    def switch_expression(self):
        """切换表情"""
        # 这里可以根据逻辑来决定换哪张图片
        self.load_image("./tachie/Murasame/嘲笑.png")

if __name__ == "__main__":
    root = tk.Tk()
    app = CharacterDisplay(root)
    root.mainloop()
