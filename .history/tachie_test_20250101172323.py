import tkinter as tk
from PIL import Image, ImageTk

class CharacterDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("动漫人物立绘展示")

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack(fill="both", expand=True)

        # 加载图片并创建图像对象
        self.character_image = Image.open("happy.png")
        self.character_photo = ImageTk.PhotoImage(self.character_image)
        self.character_image_id = self.canvas.create_image(400, 300, image=self.character_photo)

        # 创建输入框
        self.text_box = tk.Entry(root, font=("Arial", 14))
        self.text_box.place(x=400, y=350, anchor="center")

        # 设置拖动和缩放的初始位置和大小
        self.offset_x = 0
        self.offset_y = 0
        self.scale_factor = 1.0

        # 绑定鼠标事件
        self.canvas.bind("<B1-Motion>", self.drag_image)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<MouseWheel>", self.zoom_image)

        # 为输入框添加鼠标事件
        self.text_box.bind("<B1-Motion>", self.drag_text_box)
        self.text_box.bind("<ButtonRelease-1>", self.stop_drag_text_box)

        self.dragging_image = False
        self.dragging_text_box = False

    def drag_image(self, event):
        """拖动图片"""
        if self.dragging_image:
            dx = event.x - self.offset_x
            dy = event.y - self.offset_y
            self.canvas.move(self.character_image_id, dx, dy)
            self.canvas.move(self.text_box, dx, dy)  # 同时拖动输入框
            self.offset_x = event.x
            self.offset_y = event.y

    def drag_text_box(self, event):
        """拖动文本框"""
        if self.dragging_text_box:
            dx = event.x - self.offset_x
            dy = event.y - self.offset_y
            self.text_box.place(x=self.text_box.winfo_x() + dx, y=self.text_box.winfo_y() + dy)
            self.offset_x = event.x
            self.offset_y = event.y

    def stop_drag(self, event):
        """停止拖动图片"""
        self.dragging_image = False

    def stop_drag_text_box(self, event):
        """停止拖动文本框"""
        self.dragging_text_box = False

    def zoom_image(self, event):
        """缩放图片"""
        if event.delta > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor /= 1.1

        new_width = int(self.character_image.width * self.scale_factor)
        new_height = int(self.character_image.height * self.scale_factor)
        resized_image = self.character_image.resize((new_width, new_height), Image.ANTIALIAS)
        self.character_photo = ImageTk.PhotoImage(resized_image)

        # 更新图片
        self.canvas.itemconfig(self.character_image_id, image=self.character_photo)

        # 调整输入框大小
        font_size = int(14 * self.scale_factor)
        self.text_box.config(font=("Arial", font_size))

    def start_drag_image(self, event):
        """开始拖动图片"""
        self.offset_x = event.x
        self.offset_y = event.y
        self.dragging_image = True

    def start_drag_text_box(self, event):
        """开始拖动文本框"""
        self.offset_x = event.x
        self.offset_y = event.y
        self.dragging_text_box = True

if __name__ == "__main__":
    root = tk.Tk()
    app = CharacterDisplay(root)
    root.mainloop()
