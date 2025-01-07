import sys
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from whisperStream_module import SpeechStreamRecognition
import logging

# 获取根记录器
logger = logging.getLogger("micButton_module")


class RecognitionThread(QThread):
    def __init__(self, recognizer):
        super().__init__()
        self.recognizer = recognizer

    def run(self):
        # 开始流式语音识别
        self.recognizer.start_streaming()

    def stop(self):
        self.recognizer.stop_streaming()


class MicButton(QWidget):
    def __init__(self, main_settings):
        super().__init__()

        # 初始化语音识别器
        self.recognizer = SpeechStreamRecognition(main_settings)

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

        # 创建识别线程
        self.recognition_thread = RecognitionThread(self.recognizer)
        self.recognizer.update_text_signal.connect(self.on_recognition_update)
        self.recognizer.recording_ended_signal.connect(self.on_recognition_complete)

    def toggle_recording(self):
        if self.recognizer._is_running:
            # 如果语音识别正在进行，停止线程
            self.recognition_thread.stop()
        else:
            self.button.setText("🎤")  # 保证按钮显示麦克风图标
            self.button.setStyleSheet(
                "background-color: orange; border-radius: 5px;"
            )  # 录音中状态，按钮变橙色
            self.recognition_thread.start()  # 启动识别线程

    def on_recognition_update(self, text):
        # 实时更新文本显示
        print(f"实时识别结果: {text}")

    def on_recognition_complete(self):
        self.button.setText("🎤")  # 保持麦克风图标
        self.button.setStyleSheet(
            "background-color: green; border-radius: 5px;"
        )  # 识别完成状态，按钮变绿色

        # 在1秒后将按钮恢复为白色
        QTimer.singleShot(1000, self.reset_button)

        print("识别完成，停止录音")

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
