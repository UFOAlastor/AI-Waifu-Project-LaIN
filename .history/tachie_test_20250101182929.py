import tkinter as tk
from PIL import Image, ImageTk, ImageDraw


class TachieDisplay:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")
        self.root.overrideredirect(True)  # 去掉窗口边框
        self.root.attributes("-transparentcolor", "black")  # 设置透明背景
        self.root.configure(bg="black")

        # 加载立绘图像
        self.character_image = Image.open("./tachie/Murasame/正常.png").convert("RGBA")
        self.character_photo = ImageTk.PhotoImage(self.character_image)

        # 创建立绘画布
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(400, 300, image=self.character_photo)

        # 初始化拖动变量
        self.offset_x = 0
        self.offset_y = 0

        # 鼠标事件绑定
        self.canvas.bind("<B1-Motion>", self.drag_window)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)

        # 创建对话框
        self.dialog_frame = tk.Frame(
            self.root,
            bg="white",
            bd=0,
            highlightthickness=0
        )
        self.dialog_frame.place(x=200, y=400, width=400, height=150)

        # 创建对话框内容
        self.dialog_label = tk.Label(
            self.dialog_frame,
            text="你",
            font=("Arial", 14),
            bg="white",
            anchor="w"
        )
        self.dialog_label.place(x=10, y=5)
        self.dialog_text = tk.Text(
            self.dialog_frame,
            font=("Arial", 14),
            bg="white",
            wrap="word",
            height=5,
            bd=0,
            highlightthickness=0
        )
        self.dialog_text.place(x=10, y=35, width=380, height=100)

        # 关闭按钮
        self.close_button_image = self.create_rounded_button(20, 20, "red", "×")
        self.close_button = tk.Button(
            self.root,
            image=self.close_button_image,
            command=self.root.destroy,
            bg="red",
            bd=0,
            highlightthickness=0
        )
        self.close_button.place(x=760, y=10)

    def create_rounded_button(self, width, height, color, text):
        """创建圆角关闭按钮图像"""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, width, height), fill=color)
        draw.text(
            (width // 3, height // 4),
            text,
            fill="white",
            anchor="mm",
            align="center"
        )
        return ImageTk.PhotoImage(img)

    def start_drag(self, event):
        """记录拖动起始位置"""
        self.offset_x = event.x
        self.offset_y = event.y

    def drag_window(self, event):
        """拖动窗口"""
        x = self.root.winfo_pointerx() - self.offset_x
        y = self.root.winfo_pointery() - self.offset_y
        self.root.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TachieDisplay(root)
    root.mainloop()
