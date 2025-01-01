import sys
import json
from PyQt5.QtCore import Qt, QEvent, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QPushButton,
)
from PyQt5.QtCore import pyqtSignal


# 模型请求线程
class ModelRequestThread(QThread):
    # 定义一个信号，发送模型的回应文本
    response_received = pyqtSignal(str)

    def __init__(self, input_text):
        super().__init__()
        self.input_text = input_text

    def run(self):
        # 模拟获取模型回应
        # 这里你可以替换为实际的模型请求代码
        import time
        time.sleep(2)  # 模拟延迟
        response = "这是模型的回应"  # 模拟的模型回应
        self.response_received.emit(response)


class TachieDisplay(QMainWindow):
    text_sent = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.is_non_user_input = False  # 是否为非用户输入内容标记

        self.settings = self.load_settings("./config.json")
        self.window_width = self.settings.get("window_width", 500)
        self.window_height = self.settings.get("window_height", 700)
        self.dialog_x = self.settings.get("dialog_x", self.window_width)
        self.dialog_y = self.settings.get("dialog_y", self.window_height * 0.5)
        self.dialog_width = self.settings.get("dialog_width", self.window_width)
        self.dialog_height = self.settings.get(
            "dialog_height", self.window_height * 0.3
        )
        self.dialog_opacity = self.settings.get("dialog_opacity", 0.8)

        # Set up the window with transparent background
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove the window frame
        self.setAttribute(Qt.WA_TranslucentBackground)  # Transparent window background
        self.setFixedSize(self.window_width, self.window_height)
        self.setStyleSheet(
            "background-color: transparent;"
        )  # Make the whole window transparent

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

        # Dialog box setup (with transparency)
        self.dialog_widget = QWidget(self)
        self.dialog_widget.setGeometry(
            int(self.dialog_x),
            int(self.dialog_y),
            int(self.dialog_width),
            int(self.dialog_height),
        )
        self.dialog_widget.setStyleSheet(
            f"background-color: rgba(255, 255, 255, {255*self.dialog_opacity}); border: 1px solid gray; border-radius: 15px;"
        )

        self.dialog_layout = QVBoxLayout(self.dialog_widget)

        self.dialog_text = QPlainTextEdit(self.dialog_widget)
        self.dialog_text.setStyleSheet(
            "font: 14pt Arial; background-color: transparent; border: none; color: #333333;"
        )
        self.dialog_text.setFixedHeight(int(self.dialog_height))
        self.dialog_text.setFixedWidth(int(self.dialog_width - 20))
        self.dialog_layout.addWidget(self.dialog_text)

        self.dialog_text.setInputMethodHints(
            Qt.ImhPreferLowercase | Qt.ImhNoAutoUppercase
        )

        self.close_button = QPushButton("×", self)
        self.close_button.setStyleSheet(
            "background-color: red; color: white; font: bold 12pt Arial; border: none; border-radius: 15%;"
        )
        self.close_button.setGeometry(
            int(self.window_width - (self.window_width - self.dialog_width) // 2 - 30),
            0,
            30,
            30,
        )
        self.close_button.clicked.connect(self.close)

        self.setStyleSheet("background-color: transparent;")

        # 确保 QPlainTextEdit 区域可以捕获点击事件
        self.dialog_text.setAttribute(Qt.WA_OpaquePaintEvent)
        self.dialog_text.setFocusPolicy(Qt.StrongFocus)
        self.dialog_text.installEventFilter(self)

        # 动态省略号定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_loading_text)

        self.loading_text = ""
        self.dots_count = 0

    def send_text(self):
        text = self.dialog_text.toPlainText().replace("\n", "\\n ").strip()
        if text:
            print(f"发送的文本: {text}")
            self.text_sent.emit(text)  # 发射信号，将文本发送出去
            self.dialog_text.clear()  # 清空文本框内容

            # 显示等待文本（动态省略号）
            self.display_loading_text()

            # 启动模型请求线程
            self.model_thread = ModelRequestThread(text)
            self.model_thread.response_received.connect(self.display_text)
            self.model_thread.start()

    def display_loading_text(self):
        """
        显示动态省略号，直到模型回应
        """
        self.loading_text = "正在思考"
        self.dots_count = 0
        self.timer.start(500)  # 每500毫秒更新一次文本

    def update_loading_text(self):
        """
        更新动态省略号
        """
        self.dots_count = (self.dots_count + 1) % 4
        self.dialog_text.setPlainText(self.loading_text + "." * self.dots_count)

    def display_text(self, content):
        """
        显示模型回应的文本
        """
        self.timer.stop()  # 停止动态省略号
        self.dialog_text.setPlainText(content)

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
