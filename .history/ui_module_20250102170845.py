# ui_module.py

import sys
import json
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QImage, QPixmap, QKeyEvent
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
from PyQt5.QtCore import QTimer


# 在 TachieDisplay 类中设置事件过滤器
class TachieDisplay(QMainWindow):
    # 定义一个信号，发送输入的文本
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
        self.dialog_widget.setStyleSheet(
            f"background-color: rgba(255, 255, 255, {255*self.dialog_opacity}); border: 1px solid gray; border-radius: 15px;"
        )

        self.dialog_layout = QVBoxLayout(self.dialog_widget)

        self.dialog_label = QLabel("LaIN 绫", self.dialog_widget)
        self.dialog_label.setStyleSheet(
            """
            font: bold 12pt Arial;
            color: #01847f;
            background: transparent;
            border: none;
            padding: 5px;
        """
        )
        self.dialog_layout.addWidget(self.dialog_label)

        # Change from QTextEdit to QPlainTextEdit
        self.dialog_text = QPlainTextEdit(self.dialog_widget)
        self.dialog_text.setStyleSheet(
            "font: 14pt Arial; background-color: transparent; border: none; color: #3c3d3d;"
        )
        self.dialog_text.setFixedHeight(int(self.dialog_height))
        self.dialog_text.setFixedWidth(int(self.dialog_width - 20))
        self.dialog_layout.addWidget(self.dialog_text)

        # 设置输入法策略
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
        # 设置 focusPolicy
        self.dialog_text.setFocusPolicy(Qt.StrongFocus)
        # 安装事件过滤器到 dialog_text
        self.dialog_text.installEventFilter(self)
        self.dialog_text.mousePressEvent = self.on_mouse_press  # 手动重写鼠标点击事件

    def eventFilter(self, obj, event):
        # 捕获回车键事件
        if obj == self.dialog_text and event.type() == QEvent.KeyPress:
            key_event = event
            # 判断是否是 ctrl+enter 按键
            if key_event.key() == Qt.Key_Return and (
                key_event.modifiers() & Qt.ControlModifier
            ):
                # ctrl+enter 时不触发 send_text，而是进行换行
                self.dialog_text.insertPlainText("\n")
                return True  # 表示事件已处理，不再传播
            elif key_event.key() == Qt.Key_Return:
                # 其他情况下触发发送文本的功能
                self.send_text()
                return True  # 表示事件已处理，不再传播
        return super().eventFilter(obj, event)

    def on_mouse_press(self, event):
        """
        捕获 QPlainTextEdit 的鼠标点击事件
        """
        if self.is_non_user_input:
            if self.timer:  # 停止打字机定时器，防止非用户文本继续显示
                self.timer.stop()
            self.dialog_text.clear()  # 清空文本框内容
            self.is_non_user_input = False  # 重置标记
        # 处理输入符号点击操作
        print("点击了文本框的输入符号区域")
        # 调用父类的事件处理方法，确保光标行为正常
        super(QPlainTextEdit, self.dialog_text).mousePressEvent(event)

    def send_text(self):
        text = self.dialog_text.toPlainText().replace("\n", "\\n ").strip()
        if text:
            print(f"发送的文本: {text}")
            self.text_sent.emit(text)  # 发射信号，将文本发送出去
            self.dialog_text.clear()  # 清空文本框内容

    def display_text(self, content, is_non_user_input=False):
        """
        显示文本内容，is_non_user_input 为 True 时表示启动提示或模型返回内容
        """
        self.is_non_user_input = is_non_user_input  # 设置是否为非用户输入内容标记
        self.dialog_text.clear()  # 清空文本框内容
        self.dialog_text.setPlainText("")  # 清空文本框内容
        self.current_char_index = 0  # 当前字符索引
        self.content = content  # 存储要显示的完整文本

        # 设置每个字符的延迟时间（可以根据需要调整）
        self.typing_speed = 100  # 每个字符之间的延迟 100 毫秒

        # 设置定时器，模拟逐个字符的显示
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_typing)
        self.timer.start(self.typing_speed)

    def on_typing(self):
        # 每次定时器触发时，显示一个字符
        if self.current_char_index < len(self.content):
            current_text = self.dialog_text.toPlainText()
            current_text += self.content[self.current_char_index]
            self.dialog_text.setPlainText(current_text)
            self.current_char_index += 1
        else:
            self.timer.stop()  # 停止定时器，表示文本已全部显示完

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
