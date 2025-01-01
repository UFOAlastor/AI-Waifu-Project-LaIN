import tkinter as tk
from PIL import Image, ImageTk
import json


class TachieDisplay:
    def __init__(self, root):
        self.root = root
        self.root.geometry("400x800")
        self.root.overrideredirect(True)  # 去掉窗口边框
        self.root.attributes("-transparentcolor", "black")  # 设置透明背景
        self.root.configure(bg="black")

        # 加载设置
        self.settings = self.load_settings("./config.json")
        self.scale = self.settings.get("scale", 1.0)  # 默认缩放比例

        # 加载立绘
        self.image_path = self.settings.get("tachie_path", "./tachie/Murasame/正常.png")
        self.character_image = Image.open(self.image_path).convert("RGBA")
        self.character_image = self.character_image.resize(
            (int(self.character_image.width * self.scale), int(self.character_image.height * self.scale))
        )
        self.character_photo = ImageTk.PhotoImage(self.character_image)

        # 创建画布
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.character_image_id = self.canvas.create_image(400, 300, image=self.character_photo)

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
        self.dialog_frame.place(
            x=self.settings.get("dialog_x", 100),
            y=self.settings.get("dialog_y", 400),
            width=self.settings.get("dialog_width", 600),
            height=self.settings.get("dialog_height", 150),
        )

        # 圆角和透明度美化
        self.dialog_frame_canvas = tk.Canvas(
            self.dialog_frame,
            bg="white",
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        self.dialog_frame_canvas.pack(fill="both", expand=True)

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
        self.dialog_text.place(x=10, y=35, width=580, height=80)

        # 设置窗口透明度
        self.root.attributes("-alpha", self.settings.get("dialog_opacity", 0.9))  # 默认透明度 90%

        # 绑定回车事件
        self.dialog_text.bind("<Return>", self.send_text)

        # 添加关闭按钮
        self.close_button = tk.Button(
            self.root, text="关闭", command=self.root.destroy, bg="red", fg="white"
        )
        self.close_button.place(x=760, y=10)

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


if __name__ == "__main__":
    root = tk.Tk()
    app = TachieDisplay(root)
    root.mainloop()
