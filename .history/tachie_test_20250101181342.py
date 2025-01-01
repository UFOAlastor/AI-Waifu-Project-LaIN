import tkinter as tk
from PIL import Image, ImageTk, ImageResampling


class TachieDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("立绘展示")
        self.root.geometry("800x600")
        self.root.overrideredirect(True)  # 移除窗口边框
        self.root.configure(bg="black")  # 设置背景色为黑色

        # 加载立绘
        self.image_path = "./tachie/Murasame/正常.png"
        self.character_image = Image.open(self.image_path).convert("RGBA")
        self.scale_factor = 1.0
        self.character_photo = ImageTk.PhotoImage(self.character_image)
        self.character_image_id = None

        # 创建画布
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.character_image_id = self.canvas.create_image(400, 300, image=self.character_photo)

        # 初始化拖动变量
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False

        # 鼠标事件绑定
        self.canvas.bind("<B1-Motion>", self.drag_image)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<MouseWheel>", self.zoom_image)

        # 添加对话框
        self.dialog_frame = tk.Frame(self.root, bg="#222", height=100)
        self.dialog_frame.pack(side="bottom", fill="x")
        self.dialog_text = tk.Label(
            self.dialog_frame, text="", font=("Arial", 14), fg="white", bg="#222", anchor="w"
        )
        self.dialog_text.pack(side="left", padx=10, fill="both", expand=True)
        self.dialog_input = tk.Entry(self.dialog_frame, font=("Arial", 14), bg="#333", fg="white")
        self.dialog_input.pack(side="right", padx=10)
        self.dialog_input.bind("<Return>", self.display_text)  # 按回车调用显示文本

        # 移动窗口功能
        self.root.bind("<B3-Motion>", self.move_window)  # 右键拖动窗口

    def start_drag(self, event):
        """记录拖动起始位置"""
        self.offset_x = event.x
        self.offset_y = event.y
        self.dragging = True

    def stop_drag(self, event):
        """停止拖动"""
        self.dragging = False

    def drag_image(self, event):
        """拖动立绘"""
        if self.dragging:
            dx = event.x - self.offset_x
            dy = event.y - self.offset_y
            self.canvas.move(self.character_image_id, dx, dy)

    def zoom_image(self, event):
        """缩放立绘"""
        if event.delta > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor /= 1.1

        new_width = int(self.character_image.width * self.scale_factor)
        new_height = int(self.character_image.height * self.scale_factor)
        resized_image = self.character_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.character_photo = ImageTk.PhotoImage(resized_image)
        self.canvas.itemconfig(self.character_image_id, image=self.character_photo)

    def display_text(self, event=None):
        """显示对话框中的文本"""
        user_text = self.dialog_input.get()
        self.dialog_text.config(text=user_text)
        self.dialog_input.delete(0, tk.END)

    def move_window(self, event):
        """通过右键拖动窗口"""
        x = self.root.winfo_pointerx() - self.offset_x
        y = self.root.winfo_pointery() - self.offset_y
        self.root.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TachieDisplay(root)
    root.mainloop()
