import tkinter as tk
from PIL import Image, ImageTk
import json

class TachieDisplay:
    def __init__(self, root):
        self.root = root
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

        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.overrideredirect(True)
        self.root.configure(bg="black")
        self.root.attributes("-transparentcolor", "black")

        if self.settings.get("always_on_top", False):
            self.root.attributes("-topmost", True)

        # Use a PNG with transparent background
        self.image_path = (
            self.settings.get("tachie_path", "./tachie/Murasame/") + "正常.png"
        )
        self.character_image = Image.open(self.image_path).convert("RGBA")

        # Scaling the image to fit within the window size while preserving transparency
        image_width, image_height = self.character_image.size
        scale_width = self.window_width / image_width
        scale_height = self.window_height / image_height
        self.scale = min(scale_width, scale_height)

        self.character_image = self.character_image.resize(
            (int(image_width * self.scale), int(image_height * self.scale))
        )
        self.character_photo = ImageTk.PhotoImage(self.character_image)

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.character_image_id = self.canvas.create_image(
            400, 300, image=self.character_photo
        )

        self.offset_x = 0
        self.offset_y = 0
        self.canvas.bind("<B1-Motion>", self.drag_window)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)

        # Dialog box setup
        self.dialog_canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.dialog_canvas.place(
            x=self.dialog_x,
            y=self.dialog_y,
            width=self.dialog_width,
            height=self.dialog_height,
        )
        self.dialog_canvas.create_rectangle(
            0,
            0,
            self.dialog_width,
            self.dialog_height,
            fill="white",
            stipple="gray25",
        )

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

        self.dialog_text.bind("<Return>", self.send_text)

        self.close_button = tk.Button(
            self.root,
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

        self.root.bind("<Configure>", self.on_resize)

    def send_text(self, event=None, text=None):
        if text is None:
            text = self.dialog_text.get("1.0", "end-1c").strip()
        print(f"发送的文本: {text}")
        self.dialog_text.delete("1.0", "end")
        self.dialog_text.insert("1.0", text)
        return "break"

    def display_text(self, content):
        self.dialog_text.delete("1.0", "end")
        self.dialog_text.insert("1.0", content)

    def start_drag(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def drag_window(self, event):
        x = self.root.winfo_pointerx() - self.offset_x
        y = self.root.winfo_pointery() - self.offset_y
        self.root.geometry(f"+{x}+{y}")

    def load_settings(self, file_path):
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
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        self.canvas.coords(self.character_image_id, width / 2, height / 2)

        self.dialog_canvas.place(
            x=(width - self.dialog_width) // 2,
            y=height // 2,
            width=self.dialog_width,
            height=self.dialog_height,
        )

        self.close_button.place(
            x=width - (width - self.dialog_width) // 2 - 30,
            y=0,
            width=30,
            height=30,
        )
        self.close_button.lift()


if __name__ == "__main__":
    root = tk.Tk()
    app = TachieDisplay(root)
    root.mainloop()
