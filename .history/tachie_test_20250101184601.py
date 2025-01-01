import tkinter as tk
from PIL import Image, ImageTk
import json


class TachieDisplay:
    def __init__(self, root):
        self.root = root

        # 加载设置
        self.settings = self.load_settings("./config.json")

        # 设置窗口大小
        self.window_width = self.settings.get("window_width", 600)
        self.window_height = self.settings.get("window_height", 800)
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.overrideredirect(True)  # 去掉窗口边框
        self.root.configure(bg="black")

        # 设置窗口背景透明
        self.root.attributes("-transparentcolor", "black")

        self.scale = self.settings.get("scale", 1.0)  # 默认缩放比例

        # 加载立绘
        self.image_path = self.settings.get("tachie_path", "./tachie/Murasame/正常.png")
        self.character_image = Image.open(self.image_path).convert("RGBA")

        # 获取图片尺寸，计算等比例缩放
        self.original_width, self.original_height = self.character_image.size
        self.update_image_size()

        # 将缩放后的图片转换为 tkinter 可用的格式
        self.character_photo = ImageTk.PhotoImage(self.character_image)

        # 创建画布
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.character_image_id = self.canvas.create_image(
            self.window_width / 2, self.window_height / 2, image=self.character_photo
        )

        # 初始化拖动变量
        self.offset_x = 0
        self.offset_y = 0

        # 鼠标事件绑定
        self.canvas.bind("<B1-Motion>", self.drag_window)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)

        # 创建对话框
        self.dialog_frame = tk.Frame(self.root, bg="white", bd=0, highlightthickness=0)
        self.update_dialog_position()

        # 创建对话框内容
        self.dialog_label = tk.Label(
            self.dialog_frame, text="你", font=("Arial", 14), bg="white", anchor="w"
        )
        self.dialog_label.place(x=10, y=5)
        self.dialog_text = tk.Text(
            self.dialog_frame,
            font=("Arial", 14),
            bg="white",
            wrap="word",
            height=5,
            bd=0,
            highlightthickness=0,
        )
        self.dialog_text.place(x=10, y=35, width=self.dialog_width - 20, height=80)

        # 设置窗口透明度
        self.root.attributes(
            "-alpha", self.settings.get("dialog_opacity", 0.9)
        )  # 默认透明度 90%

        # 绑定回车事件
        self.dialog_text.bind("<Return>", self.send_text)

        # 添加关闭按钮（位于对话框右上角）
        self.close_button = tk.Button(
            self.dialog_frame,
            text="×",
            command=self.root.destroy,
            bg="red",
            fg="white",
            font=("Arial", 12, "bold"),
        )
        self.close_button.place(x=self.dialog_width - 30, y=10, width=30, height=30)

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

    def update_image_size(self):
        """根据窗口尺寸动态更新立绘的大小"""
        # 获取新的窗口尺寸
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        # 计算等比例缩放的最大尺寸
        scale_width = window_width * 0.5  # 设置立绘宽度最大为窗口宽度的一半
        scale_height = window_height * 0.5  # 设置立绘高度最大为窗口高度的一半

        # 根据宽度和高度计算缩放比例
        scale_factor = min(
            scale_width / self.original_width, scale_height / self.original_height
        )

        # 更新立绘尺寸
        new_width = int(self.original_width * scale_factor)
        new_height = int(self.original_height * scale_factor)

        # 确保宽度和高度都大于0
        if new_width <= 0 or new_height <= 0:
            new_width = max(1, self.original_width)
            new_height = max(1, self.original_height)

        self.character_image = self.character_image.resize((new_width, new_height))
        self.character_photo = ImageTk.PhotoImage(self.character_image)

        # 更新立绘显示
        self.canvas.itemconfig(self.character_image_id, image=self.character_photo)

    def update_dialog_position(self):
        """根据窗口尺寸更新对话框位置和大小"""
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        # 计算对话框宽度和高度
        self.dialog_width = int(window_width * 0.8)  # 对话框宽度为窗口宽度的80%
        self.dialog_height = int(
            window_height * 0.1875
        )  # 对话框高度为窗口高度的150/800
        self.dialog_frame.place(
            x=(window_width - self.dialog_width) // 2,
            y=window_height - int(window_height * 0.25) - self.dialog_height,
            width=self.dialog_width,
            height=self.dialog_height,
        )

    def on_resize(self, event):
        """动态调整部件位置"""
        self.update_image_size()
        self.update_dialog_position()

        width = self.root.winfo_width()
        height = self.root.winfo_height()

        # 调整关闭按钮位置
        self.close_button.place(x=self.dialog_width - 30, y=10)

        # 调整人物立绘位置
        self.canvas.coords(self.character_image_id, width / 2, height / 2)


if __name__ == "__main__":
    root = tk.Tk()
    app = TachieDisplay(root)
    root.mainloop()
