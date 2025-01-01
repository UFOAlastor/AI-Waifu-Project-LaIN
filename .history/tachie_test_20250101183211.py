import tkinter as tk
import json
from PIL import Image, ImageTk, ImageDraw


class TachieDisplay:
    def __init__(self, root, settings_path="config.json"):
        self.root = root
        self.settings = self.load_settings(settings_path)

        # 设置窗口尺寸
        self.root.geometry(f"{self.settings['window_width']}x{self.settings['window_height']}")
        self.root.overrideredirect(True)  # 去掉窗口边框
        self.root.attributes("-transparentcolor", self.settings["transparent_color"])  # 设置透明背景
        self.root.configure(bg=self.settings["background_color"])

        # 加载立绘图像
        self.character_image = Image.open(self.settings["character_image_path"]).convert("RGBA")
        self.character_photo = ImageTk.PhotoImage(self.character_image)

        # 创建立绘画布
        self.canvas = tk.Canvas(self.root, bg=self.settings["background_color"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(
            self.settings["window_width"] // 2, self.settings["window_height"] // 2, image=self.character_photo
        )

        # 初始化拖动变量
        self.offset_x = 0
        self.offset_y = 0

        # 鼠标事件绑定
        self.canvas.bind("<B1-Motion>", self.drag_window)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)

        # 创建对话框
        self.dialog_frame = tk.Frame(
            self.root,
            bg=self.settings["dialog_background_color"],
            bd=0,
            highlightthickness=0
        )
        self.dialog_frame.place(
            x=self.settings["dialog_position"][0],
            y=self.settings["dialog_position"][1],
            width=self.settings["dialog_width"],
            height=self.settings["dialog_height"]
        )

        # 创建对话框内容
        self.dialog_label = tk.Label(
            self.dialog_frame,
            text="你",
            font=("Arial", 14),
            bg=self.settings["dialog_background_color"],
            anchor="w"
        )
        self.dialog_label.place(x=10, y=5)
        self.dialog_text = tk.Text(
            self.dialog_frame,
            font=("Arial", 14),
            bg=self.settings["dialog_background_color"],
            wrap="word",
            height=5,
            bd=0,
            highlightthickness=0
        )
        self.dialog_text.place(x=10, y=35, width=self.settings["dialog_width"] - 20, height=100)

        # 创建关闭按钮
        self.close_button_image = self.create_rounded_button(
            self.settings["close_button_size"][0],
            self.settings["close_button_size"][1],
            self.settings["close_button_color"],
            self.settings["close_button_text"]
        )
        self.close_button = tk.Button(
            self.root,
            image=self.close_button_image,
            command=self.root.destroy,
            bg=self.settings["close_button_color"],
            bd=0,
            highlightthickness=0
        )
        self.close_button.place(
            x=self.settings["window_width"] - 30, y=10
        )

    def load_settings(self, path):
        """加载设置文件"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

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
