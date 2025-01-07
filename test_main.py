import sys, json
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from whisper_module import SpeechRecognition
import logging, logging_config

# 初始化日志配置
logging_config.setup_logging()
# 获取根记录器
logger = logging.getLogger()


def load_settings(file_path="./config.json"):
    """加载配置文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
            return settings
    except FileNotFoundError:
        logger.error(f"未找到设置文件: {file_path}")
    except json.JSONDecodeError:
        logger.error(f"设置文件格式错误: {file_path}")
    return {}


# 语音识别线程
class SpeechRecognitionThread(QThread):
    recognition_complete = pyqtSignal(str)  # 语音识别完成的信号
    interrupted = pyqtSignal()  # 打断信号

    def __init__(self, recognizer, parent=None):
        super().__init__(parent)
        self.recognizer = recognizer
        self._is_running = True  # 控制线程是否继续运行

    def run(self):
        try:
            # 直接启动识别，识别结束后发出信号
            result = self.recognizer.start_speech_input()
            if self._is_running:  # 如果没有被打断才发射识别完成信号
                self.recognition_complete.emit(result)
        except Exception as e:
            logger.error(f"语音识别错误: {e}")

    def stop(self):
        """停止线程"""
        self._is_running = False
        self.interrupted.emit()


# 主窗口类
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        settings = load_settings()

        self.setWindowTitle("AI 助手")
        self.setGeometry(100, 100, 200, 200)

        # 初始化语音识别器
        self.recognizer = SpeechRecognition(settings)

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

        self.recognition_thread = None

    def toggle_recording(self):
        if self.recognition_thread and self.recognition_thread.isRunning():
            # 如果语音识别正在进行，停止线程
            self.recognition_thread.stop()
            self.button.setStyleSheet(
                "background-color: white; border-radius: 5px;"
            )  # 录音中途停止，恢复白色
            self.button.setText("🎤")  # 恢复麦克风图标
        else:
            self.button.setText("🎤")  # 保证按钮显示麦克风图标
            self.button.setStyleSheet(
                "background-color: orange; border-radius: 5px;"
            )  # 录音中状态，按钮变橙色
            self.recognition_thread = SpeechRecognitionThread(self.recognizer)
            self.recognition_thread.recognition_complete.connect(
                self.on_recognition_complete
            )
            self.recognition_thread.interrupted.connect(self.on_interrupted)
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
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
