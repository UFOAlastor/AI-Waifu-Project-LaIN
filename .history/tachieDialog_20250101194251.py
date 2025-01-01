import tkinter as tk
from PIL import Image, ImageTk
import json


class TachieDisplay:
    def __init__(self, root):
        self.root = root

        # 加载设置
        self.settings = self.load_settings("./config.json")
        self.window_width = self.settings.get("window_width", 500)
        self.window_height = self.settings.get("window_height", 700)
        self.dialog_x = self.settings.get("dialog_x", self.window_width * 0.1)
        self.dialog_y = self.settings.get("dialog_y", self.window_height * 0.5)
        self.dialog_width = self.settings.get("dialog_width", self.window_width * 0.8)
        self.dialog_height = self.settings.get(
            "dialog_height", self.window_height * 0.2
        )
        self.dialog_opacity = self.settings.get("dialog_opacity", 0.8)

        # 设置窗口大小
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.overrideredirect(True)  # 去掉窗口边框
        self.root.configure(bg="black")

        # 设置窗口背景透明
        self.root.attributes("-transparentcolor", "black")

        # 检查是否需要设置窗口始终置顶
        if self.settings.get("always_on_top", False):  # 默认值为False
            self.root.attributes("-topmost", True)

        # 加载立绘图片
        self.image_path = (
            self.settings.get("tachie_path", "./tachie/Murasame/") + "正常.png"
        )
        self.character_image = Image.open(self.image_path).convert("RGBA")
        # 加载立绘
        image_width, image_height = self.character_image.size

        # 计算适合窗口的缩放比例
        scale_width = self.window_width / image_width
        scale_height = self.window_height / image_height

        # 选择较小的缩放比例，确保图片完整显示在窗口内
        self.scale = self.settings.get(
            "scale", min(scale_width, scale_height)
        )  # 默认缩放比例

        # 按照计算出的比例调整图片大小
        self.character_image = self.character_image.resize(
            (
                int(image_width * self.scale),
                int(image_height * self.scale),
            )
        )
        self.character_photo = ImageTk.PhotoImage(self.character_image)

        # 创建画布
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.character_image_id = self.canvas.create_image(
            400, 300, image=self.character_photo
        )

        # 初始化拖动变量
        self.offset_x = 0
        self.offset_y = 0

        # 鼠标事件绑定
        self.canvas.bind("<B1-Motion>", self.drag_window)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)

        # 创建对话框背景 Canvas 以实现透明度
        self.dialog_canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.dialog_canvas.place(
            x=self.dialog_x,
            y=self.dialog_y,
            width=self.dialog_width,
            height=self.dialog_height,
        )

        # 设置对话框透明度
        self.dialog_canvas.create_rectangle(
            0,
            0,
            self.dialog_width,
            self.dialog_height,
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

        # 绑定回车事件
        self.dialog_text.bind("<Return>", self.send_text)

        # 重新设置关闭按钮
        self.close_button = tk.Button(
            self.root,  # 直接放在根窗口上
            text="×",
            command=self.root.destroy,
            bg="red",
            fg="white",
            font=("Arial", 12, "bold"),
        )
        self.close_button.place(
            x=self.window_width - (self.window_width - self.dialog_width) // 2 - 30,
            y=0,
            width=30,
            height=30,
        )

        # 绑定窗口大小变化事件
        self.root.bind("<Configure>", self.on_resize)

    def send_text(self, event):
        """处理回车键发送文本"""
        text = self.dialog_text.get("1.0", "end-1c").strip()
        print(f"发送的文本: {text}")  # 这里可以进一步处理文本
        self.dialog_text.delete("1.0", "end")
        return "break"  # 防止回车换行

    def display_text(self, content):
        """显示文本接口"""
        self.dialog_text.delete("1.0", "end")
        self.dialog_text.insert("1.0", content)

    def start_drag(self, event):
        """记录拖动起始位置"""
        self.offset_x = event.x
        self.offset_y = event.y

    def drag_window(self, event):
        """拖动窗口"""
        x = self.root.winfo_pointerx() - self.offset_x
        y = self.root.winfo_pointery() - self.offset_y
        self.root.geometry(f"+{x}+{y}")

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

    def on_resize(self, event):
        """动态调整部件位置"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        # 调整人物立绘位置
        self.canvas.coords(self.character_image_id, width / 2, height / 2)

        # 调整对话框位置
        self.dialog_canvas.place(
            x=(width - self.dialog_width) // 2,
            y=height - (height - self.dialog_height) // 3,
            width=self.dialog_width,
            height=self.dialog_height,
        )

        # 调整关闭按钮位置
        self.close_button.place(
            x=width - (width - self.dialog_width) // 2 - 30,
            y=0,
            width=30,
            height=30,
        )

        # 确保关闭按钮在最上层
        self.close_button.lift()


if __name__ == "__main__":
    root = tk.Tk()
    app = TachieDisplay(root)
    root.mainloop()
