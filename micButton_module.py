# micButton_module.py

import sys
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from whisper_module import SpeechRecognition
import logging

# 获取根记录器
logger = logging.getLogger("micButton_module")


# 语音识别线程
class SpeechRecognitionThread(QThread):
    recognition_complete = pyqtSignal(str)  # 语音识别完成的信号

    def __init__(self, recognizer, parent=None):
        super().__init__(parent)
        self.recognizer = recognizer
        self.result = ""

    def run(self):
        # 直接启动识别，识别结束后发出信号
        self.result = self.recognizer.start_speech_input()
        self.recognition_complete.emit(self.result)

    def stop(self):
        """打断线程, 直接发送结果"""
        self.recognizer.stop_speech_input()


class MicButton(QWidget):
    def __init__(self, main_settings):
        super().__init__()

        # 初始化语音识别器
        self.recognizer = SpeechRecognition(main_settings)

        # 创建按钮
        self.button = QPushButton("🎤", self)  # 使用麦克风图标作为按钮文字
        self.button.setFixedSize(30, 30)  # 设置按钮大小
        self.button.setStyleSheet(
            "background-color: white; border-radius: 5px;"
        )  # 初始状态白色背景
        self.button.setText("🎤")  # 设置初始图标
        self.button.clicked.connect(self.toggle_recording)

        # 创建布局
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.recognition_thread = SpeechRecognitionThread(self.recognizer)
        self.recognition_thread.recognition_complete.connect(
            self.on_recognition_complete
        )

    def toggle_recording(self):
        if self.recognition_thread and self.recognition_thread.isRunning():
            # 如果语音识别正在进行，停止线程
            self.recognition_thread.stop()
        else:
            self.button.setText("🎤")  # 保证按钮显示麦克风图标
            self.button.setStyleSheet(
                "background-color: orange; border-radius: 5px;"
            )  # 录音中状态，按钮变橙色
            self.recognition_thread.start()

    def on_recognition_complete(self, result):
        self.button.setText("🎤")  # 保持麦克风图标
        self.button.setStyleSheet(
            "background-color: green; border-radius: 5px;"
        )  # 识别完成状态，按钮变绿色

        # 在1秒后将按钮恢复为白色
        QTimer.singleShot(1000, self.reset_button)

        print(f"识别结果：{result}")  # 打印识别的文本

    def on_interrupted(self):
        self.button.setText("🎤")  # 恢复麦克风图标
        self.button.setStyleSheet(
            "background-color: white; border-radius: 5px;"
        )  # 恢复按钮为白色

    def reset_button(self):
        self.button.setStyleSheet(
            "background-color: white; border-radius: 5px;"
        )  # 恢复按钮为白色


# 启动应用
if __name__ == "__main__":
    import logging_config, json

    # 初始化日志配置
    logging_config.setup_logging()
    with open("./config.json", "r", encoding="utf-8") as f:
        settings = json.load(f)

    app = QApplication(sys.argv)
    window = MicButton(settings)
    window.show()
    sys.exit(app.exec_())
