import tkinter as tk
from PIL import Image, ImageTk


class TachieDisplay:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")
        self.root.overrideredirect(True)  # 去掉窗口边框
        self.root.attributes("-transparentcolor", "black")  # 设置透明背景
        self.root.configure(bg="black")

        # 加载立绘
        self.image_path = "./tachie/Murasame/正常.png"
        self.character_image = Image.open(self.image_path).convert("RGBA")
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
        self.dialog_frame = tk.Frame(self.root, bg="#EEEEEE", height=100)
        self.dialog_frame.place(x=100, y=400, width=600, height=150)  # 自定义位置
        self.dialog_label = tk.Label(
            self.dialog_frame, text="你", font=("Arial", 14), bg="#EEEEEE", anchor="w"
        )
        self.dialog_label.pack(anchor="nw", padx=10, pady=5)
        self.dialog_text = tk.Text(
            self.dialog_frame, font=("Arial", 14), bg="#FFFFFF", wrap="word", height=5
        )
        self.dialog_text.pack(fill="both", expand=True, padx=10, pady=5)

        # 添加关闭按钮
        self.close_button = tk.Button(
            self.root, text="关闭", command=self.root.destroy, bg="red", fg="white"
        )
        self.close_button.place(x=760, y=10)

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
