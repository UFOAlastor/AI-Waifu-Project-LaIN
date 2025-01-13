# ui_module.py

import sys
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QPushButton,
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QTimer
import re, markdown
import logging

# 获取根记录器
logger = logging.getLogger("ui_module")

# 被继承的模块
from micButton_module import MicButton


# 在 UIDisplay 类中设置事件过滤器
class UIDisplay(QMainWindow, MicButton):
    text_sent = pyqtSignal(str)  # 发送对话框文本信号

    def __init__(self, main_settings):
        super().__init__(main_settings)  # python的继承按 MRO 顺序传递参数
        self.is_non_user_input = False  # 是否为非用户输入内容标记

        self.setWindowTitle("Project LaIN")
        self.setWindowIcon(QIcon("./ico/lin.ico"))  # 设置图标

        self.settings = main_settings
        self.window_width = self.settings.get("window_width", 500)
        self.window_height = self.settings.get("window_height", 700)
        self.dialog_x = self.settings.get("dialog_x", self.window_width)
        self.dialog_y = self.settings.get("dialog_y", self.window_height * 0.5)
        self.dialog_width = self.settings.get("dialog_width", self.window_width)
        self.dialog_height = self.settings.get(
            "dialog_height", self.window_height * 0.3
        )
        self.dialog_opacity = self.settings.get("dialog_opacity", 0.8)
        self.label_text = self.settings.get("dialog_label", "")
        self.tachie_path = self.settings.get("tachie_path", "./tachie/Murasame/")
        self.default_tachie = self.settings.get("default_tachie", "正常")
        self.opening_tachie = self.settings.get("opening_tachie", "高兴")
        self.tachie_suffix = self.settings.get("tachie_suffix", "png")

        # 初始化时创建立绘的 QLabel 和设置拖动功能
        self.character_label = QLabel(self)
        self.character_label.setAlignment(Qt.AlignCenter)
        self.character_label.setGeometry(0, 0, self.window_width, self.window_height)
        self.offset_x = 0
        self.offset_y = 0
        self.character_label.mousePressEvent = self.start_drag
        self.character_label.mouseMoveEvent = self.drag_window
        self.cached_images = {}  # 用于缓存加载过的图像

        # 设置主窗口背景透明
        self.setWindowFlags(Qt.FramelessWindowHint)  # 去除 window frame
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明窗口背景
        self.setFixedSize(self.window_width, self.window_height)
        self.setStyleSheet("background-color: transparent;")  # 使整个窗口透明

        # 整个窗口始终置顶
        if self.settings.get("always_on_top", False):
            self.setWindowFlag(Qt.WindowStaysOnTopHint)

        # 开场立绘显示
        self.tachie_display(self.opening_tachie)

        # 设置2.5秒后执行回调函数，切换回默认立绘
        QTimer.singleShot(2500, lambda: self.tachie_display(self.default_tachie))

        # 对话框设置（带透明度）
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

        if not self.label_text == "":  # label 标签显示 修改此处以自定义标签外观
            self.dialog_label = QLabel(self.label_text, self.dialog_widget)
            self.dialog_label.setStyleSheet(
                """
                font: bold 12pt Arial;
                color: #818181;
                background: transparent;
                border: none;
                padding: 5px;
            """
            )
            self.dialog_layout.addWidget(self.dialog_label)

        self.dialog_text = QTextEdit(self.dialog_widget)
        self.dialog_text.setStyleSheet(
            "font: 14pt Arial; background-color: transparent; border: none; color: #2f2f2f;"
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

        # 录音按钮位置调整
        self.mic_button.setGeometry(
            10,
            int(self.dialog_y) - 30,
            30,
            30,
        )

        # 提升录音按钮层次, 避免遮挡
        self.mic_button.raise_()

        # 绑定语音识别信号量给对话框更新
        self.recognizer.update_text_signal.connect(self.whisper_stream_update)
        self.recognizer.recording_ended_signal.connect(self.send_text)

        # 打字机效果显示采用计时器实现
        self.typing_timer = QTimer(self)

    def whisper_stream_update(self, text):
        """
        语音识别结果流式追加显示文本内容，is_non_user_input 为 True 时表示启动提示或模型返回内容
        """
        if not self.recognizer_is_updating:
            self.recognizer_is_updating = True
            self.is_non_user_input = False  # 语音识别为用户输入
            self.dialog_text.clear()  # 清空文本框内容
            self.current_char_index = 0  # 当前字符索引
            self.content = text  # 初始化文本
            # 设置每个字符的延迟时间（可以根据需要调整）
            self.typing_speed = 25  # 每个字符之间的延迟 25 毫秒
            # 设置定时器，模拟逐个字符的显示
            self.current_text = ""
            self.html_closed = 0
            self.typing_timer.timeout.connect(self.on_typing_display)
            self.typing_timer.start(self.typing_speed)
        else:
            self.content += text  # 拼接文本

    def tachie_display(self, tachie_name):
        """角色立绘显示"""
        # 如果缓存中已有该图像，直接使用缓存
        if tachie_name in self.cached_images:
            self.character_image = self.cached_images[tachie_name]
        else:
            # 加载图像并缓存
            self.character_image = QImage(
                self.tachie_path + tachie_name + "." + self.tachie_suffix
            )
            self.cached_images[tachie_name] = self.character_image

        image_width, image_height = (
            max(self.character_image.width(), 100),
            max(self.character_image.height(), 100),
        )
        scale_width = self.window_width / image_width
        scale_height = self.window_height / image_height
        self.scale = min(scale_width, scale_height)

        self.character_image = self.character_image.scaled(
            int(image_width * self.scale), int(image_height * self.scale)
        )

        # 更新 QPixmap 来显示图像
        self.character_label.setPixmap(QPixmap.fromImage(self.character_image))
        self.character_label.setGeometry(0, 0, self.window_width, self.window_height)

    def start_drag(self, event):
        """窗口拖动"""
        # 拖动事件处理函数
        self.offset_x = event.x()
        self.offset_y = event.y()

    def drag_window(self, event):
        """窗口拖动"""
        # 拖动事件处理函数
        delta_x = event.x() - self.offset_x
        delta_y = event.y() - self.offset_y
        self.move(self.x() + delta_x, self.y() + delta_y)

    def eventFilter(self, obj, event):
        """回车键捕获, 用于触发对话框中回车发送操作, 支持ctrl+enter换行"""
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
        捕获 QPlainTextEdit 的鼠标点击事件, 用于对话框点击清空操作
        """
        if self.is_non_user_input:
            try:
                if self.typing_timer:  # 停止打字机定时器，防止非用户文本继续显示
                    self.typing_timer.stop()
            except Exception as e:
                logger.warning(f"self.timer停止错误: {e}")
            self.dialog_text.clear()  # 清空文本框内容
            self.is_non_user_input = False  # 重置标记
        # 处理输入符号点击操作
        logger.debug("点击了文本框的输入符号区域")
        # 调用父类的事件处理方法，确保光标行为正常
        super(QTextEdit, self.dialog_text).mousePressEvent(event)

    def send_text(self):
        """将对话框内文本发送给模型接口"""
        self.typing_timer.stop()  # 停止对话框文本显示
        text = self.dialog_text.toPlainText().replace("\n", "\\n ").strip()
        if text:
            logger.debug(f"发送的文本: {text}")
            self.text_sent.emit(text)  # 发射信号，将文本发送出去
            self.dialog_text.clear()  # 清空文本框内容

    def display_text(self, content, is_non_user_input=False):
        """
        对话框显示文本内容，is_non_user_input 为 True 时表示启动提示或模型返回内容
        """
        self.is_non_user_input = is_non_user_input  # 设置是否为非用户输入内容标记
        self.dialog_text.clear()  # 清空文本框内容
        self.current_char_index = 0  # 当前字符索引
        self.content = content  # 存储要显示的完整文本, 不进行html转义
        # 将Markdown内容转为HTML
        self.content = markdown.markdown(content)
        # # 设置定时器，模拟逐个字符的显示
        self.current_text = ""
        self.html_closed = 0
        self.typing_speed = 25  # 每个字符之间的延迟 25 毫秒
        self.typing_timer.timeout.connect(self.on_typing_display)
        self.typing_timer.start(self.typing_speed)

    def auto_complete_html_end(self, html_text):
        # 正则表达式，用于匹配HTML标签（包括带属性的标签）
        tag_pattern = r"</?([a-zA-Z0-9]+)([^>]*)>"
        # 用栈来保存当前的未闭合标签
        open_tags = []
        # 通过正则匹配标签
        matches = re.finditer(tag_pattern, html_text)
        for match in matches:
            tag = match.group(1)
            # 判断是否是自闭合标签
            if (
                html_text[match.start()] == "<" and html_text[match.start() + 1] != "/"
            ):  # 如果是开标签
                # 需要检查是否为自闭合标签
                if tag not in [
                    "area",
                    "base",
                    "br",
                    "col",
                    "embed",
                    "hr",
                    "img",
                    "input",
                    "link",
                    "meta",
                    "source",
                    "track",
                    "wbr",
                ]:
                    open_tags.append(tag)
            elif (
                html_text[match.start()] == "<" and html_text[match.start() + 1] == "/"
            ):  # 如果是闭标签
                if open_tags and open_tags[-1] == tag:
                    open_tags.pop()
        # 根据栈中的开标签，逐一补全闭合标签
        closing_tags = []
        while open_tags:
            tag = open_tags.pop()
            closing_tags.append(f"</{tag}>")
        return "".join(closing_tags)

    def on_typing_display(self):
        """每次定时器触发时, 显示一个字符"""
        # 判断html格式是否闭合 (例如: <p未闭合, <p>闭合)
        if self.current_char_index < len(self.content):
            if self.content[self.current_char_index] == ">":
                self.html_closed -= 1
            if self.content[self.current_char_index] == "<":
                self.html_closed += 1
            # 累加当前字符到 current_text
            self.current_text += self.content[self.current_char_index]
            if self.html_closed == 0:
                # 生成完整的 HTML 内容
                auto_completed_current_text = (  # 自动补全缺失的末尾
                    self.current_text + self.auto_complete_html_end(self.current_text)
                )
                self.dialog_text.setHtml(auto_completed_current_text)
            self.current_char_index += 1
        elif self.recognizer_is_updating and self.current_char_index == len(
            self.content
        ):
            # 添加对语音识别流式更新过程的挂起
            pass
        else:
            self.typing_timer.stop()  # 停止定时器，表示文本已全部显示完

    def resizeEvent(self, event):
        """窗口重置函数, 史山遗留代码(去除会导致窗口异常)"""
        width = self.width()
        height = self.height()

        self.character_label.setGeometry(0, 0, width, height)
        self.dialog_widget.move(int((width - self.dialog_width) // 2), int(height // 2))

        self.close_button.move(int(width - (width - self.dialog_width) // 2 - 30), 0)

    def closeEvent(self, event: QEvent):
        if self.recognizer._is_running:
            self.recognition_thread.stop()  # 如果语音识别正在进行，停止线程
        self.vits_speaker.vits_stop_audio()  # 停止音频播放
        event.accept()  # 正常关闭窗口


if __name__ == "__main__":
    import yaml
    import logging_config

    # 初始化日志配置
    logging_config.setup_logging()

    """加载配置文件"""
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    app = QApplication(sys.argv)
    window = UIDisplay(settings)
    window.display_text("Ciallo～(∠・ω< )⌒☆ UI模块测试提示文本", is_non_user_input=True)
    window.show()

    def test_response():
        window.display_text("你好, UI模块测试回复文本", is_non_user_input=True)

    window.text_sent.connect(test_response)
    sys.exit(app.exec_())
