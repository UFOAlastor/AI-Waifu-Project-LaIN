import sys
import json
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QKeyEvent
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QPushButton,
    QGraphicsDropShadowEffect  # 导入阴影效果
)

class TachieDisplay(QMainWindow):
    def __init__(self):
        super().__init__()

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

        # Set up the window with transparent background
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove the window frame
        self.setAttribute(Qt.WA_TranslucentBackground)  # Transparent window background
        self.setFixedSize(self.window_width, self.window_height)
        self.setStyleSheet("background-color: transparent;")  # Make the whole window transparent

        if self.settings.get("always_on_top", False):
            self.setWindowFlag(Qt.WindowStaysOnTopHint)

        # Load character image (no transparency for character image)
        self.image_path = (
            self.settings.get("tachie_path", "./tachie/Murasame/") + "正常.png"
        )
        self.character_image = QImage(self.image_path)

        image_width, image_height = (
            self.character_image.width(),
            self.character_image.height(),
        )
        scale_width = self.window_width / image_width
        scale_height = self.window_height / image_height
        self.scale = min(scale_width, scale_height)

        self.character_image = self.character_image.scaled(
            int(image_width * self.scale), int(image_height * self.scale)
        )

        # Set up QLabel to display the image (without transparency)
        self.character_label = QLabel(self)
        self.character_label.setPixmap(QPixmap.fromImage(self.character_image))
        self.character_label.setAlignment(Qt.AlignCenter)
        self.character_label.setGeometry(0, 0, self.window_width, self.window_height)

        # Set up draggable area
        self.offset_x = 0
        self.offset_y = 0
        self.character_label.mousePressEvent = self.start_drag
        self.character_label.mouseMoveEvent = self.drag_window

        # Dialog box setup (with transparency)
        self.dialog_widget = QWidget(self)
        self.dialog_widget.setGeometry(
            int(self.dialog_x),
            int(self.dialog_y),
            int(self.dialog_width),
            int(self.dialog_height),
        )
        # Remove box-shadow, we will use QGraphicsDropShadowEffect for shadow
        self.dialog_widget.setStyleSheet(
            "background-color: rgba(255, 255, 255, 180); border: 1px solid gray; border-radius: 10px;"
        )

        # Apply shadow effect to the dialog widget
        shadow_effect = QGraphicsDropShadowEffect(self.dialog_widget)
        shadow_effect.setOffset(0, 0)
        shadow_effect.setBlurRadius(15)
        shadow_effect.setColor(Qt.black)
        self.dialog_widget.setGraphicsEffect(shadow_effect)

        self.dialog_layout = QVBoxLayout(self.dialog_widget)

        self.dialog_label = QLabel("绫", self.dialog_widget)
        self.dialog_label.setStyleSheet("font: bold 14pt Arial; color: #333333;")
        self.dialog_layout.addWidget(self.dialog_label)

        # Change from QTextEdit to QPlainTextEdit
        self.dialog_text = QPlainTextEdit(self.dialog_widget)
        self.dialog_text.setStyleSheet("font: 14pt Arial; background-color: transparent; border: none; color: #333333;")
        self.dialog_text.setFixedHeight(80)
        self.dialog_text.setFixedWidth(int(self.dialog_width - 20))
        self.dialog_layout.addWidget(self.dialog_text)

        # 设置输入法策略
        self.dialog_text.setInputMethodHints(Qt.ImhPreferLowercase | Qt.ImhNoAutoUppercase)

        # 设置 focusPolicy
        self.dialog_text.setFocusPolicy(Qt.StrongFocus)

        # 设置 keyPressEvent 来捕获回车键
        self.dialog_text.keyPressEvent = self.keyPressEvent

        self.close_button = QPushButton("×", self)
        self.close_button.setStyleSheet(
            "background-color: red; color: white; font: bold 12pt Arial; border: none; border-radius: 50%;"
        )
        self.close_button.setGeometry(
            int(self.window_width - (self.window_width - self.dialog_width) // 2 - 30),
            0,
            30,
            30,
        )
        self.close_button.clicked.connect(self.close)

        self.setStyleSheet("background-color: transparent;")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return:
            self.send_text()  # 按下回车键时发送文本
        else:
            super().keyPressEvent(event)  # 处理其他按键事件

    def send_text(self):
        text = self.dialog_text.toPlainText().strip()
        print(f"发送的文本: {text}")
        self.dialog_text.clear()  # 清空文本框内容
        self.dialog_text.setPlainText("")  # 确保文本框为空

    def display_text(self, content):
        self.dialog_text.clear()
        self.dialog_text.setPlainText(content)

    def start_drag(self, event):
        self.offset_x = event.x()
        self.offset_y = event.y()

    def drag_window(self, event):
        x = event.globalX() - self.offset_x
        y = event.globalY() - self.offset_y
        self.move(x, y)

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

    def resizeEvent(self, event):
        width = self.width()
        height = self.height()

        self.character_label.setGeometry(0, 0, width, height)
        self.dialog_widget.move(int((width - self.dialog_width) // 2), int(height // 2))

        self.close_button.move(int(width - (width - self.dialog_width) // 2 - 30), 0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TachieDisplay()
    window.show()
    sys.exit(app.exec_())
