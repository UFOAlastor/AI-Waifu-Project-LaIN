import tkinter as tk
from PIL import Image, ImageTk
import json

class TachieDisplay:
    def __init__(self, root, config_file='./config.json'):
        self.root = root
        self.config_file = config_file
        self.settings = self.load_settings(config_file)
        self.setup_ui()

    def setup_ui(self):
        """ 初始化界面 """
        self.window_width = self.settings.get("window_width", 500)
        self.window_height = self.settings.get("window_height", 700)

        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.overrideredirect(True)  # 去掉窗口边框
        self.root.configure(bg="black")
        self.root.attributes("-transparentcolor", "black")

        # 加载立绘图片
        self.image_path = self.settings.get("tachie_path", "./tachie/Murasame/") + "正常.png"
        self.character_image = Image.open(self.image_path).convert("RGBA")
        image_width, image_height = self.character_image.size
        scale_width = self.window_width / image_width
        scale_height = self.window_height / image_height
        self.scale = min(scale_width, scale_height)

        self.character_image = self.character_image.resize(
            (int(image_width * self.scale), int(image_height * self.scale))
        )
        self.character_photo = ImageTk.PhotoImage(self.character_image)

        # 创建画布
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.character_image_id = self.canvas.create_image(
            400, 300, image=self.character_photo
        )

        # 创建对话框背景 Canvas 以实现透明度
        self.dialog_canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.dialog_canvas.place(
            x=self.window_width * 0.1,
            y=self.window_height * 0.5,
            width=self.window_width * 0.8,
            height=self.window_height * 0.2,
        )

        # 设置对话框透明度
        self.dialog_canvas.create_rectangle(
            0,
            0,
            self.window_width * 0.8,
            self.window_height * 0.2,
            fill="white",
            stipple="gray25",  # "gray25" 会产生透明效果
        )

        # 创建对话框内容
        self.dialog_label = tk.Label(
            self.dialog_canvas, text="绫", font=("Arial", 14), bg="white", anchor="w"
        )
        self.dialog_label.place(x=10, y=5)
        self.dialog_text = tk.Text(
            self.dialog_canvas,
            font=("Arial", 14),
            bg="white",
            wrap="word",
            height=5,
            bd=0,
            highlightthickness=0,
        )
        self.dialog_text.place(x=10, y=35, width=580, height=80)

    def load_settings(self, file_path):
        """加载设置文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"未找到设置文件: {file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"设置文件格式错误: {file_path}")
            return {}

    def update_dialog(self, text):
        """更新对话框内容"""
        self.dialog_text.delete("1.0", "end")
        self.dialog_text.insert("1.0", text)

    def display(self):
        """启动UI窗口"""
        self.root.mainloop()

