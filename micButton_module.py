# micButton_module.py

import sys
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
import logging

# 获取根记录器
logger = logging.getLogger("micButton_module")

from asr_module import SpeechRecognition


class RecognitionThread(QThread):
    def __init__(self, recognizer):
        super().__init__()
        self.recognizer = recognizer

    def run(self):
        # 开始流式语音识别
        self.recognizer.start_streaming()

    def stop(self):
        self.recognizer.stop_streaming()
        self.quit()  # 调用quit来退出线程


class MicButton(QWidget):
    def __init__(self, main_settings):
        super().__init__()

        # 初始化语音识别器
        self.recognizer = SpeechRecognition(main_settings)

        # 创建按钮
        self.mic_button = QPushButton("🎤", self)  # 使用麦克风图标作为按钮文字
        self.mic_button.setFixedSize(30, 30)  # 设置按钮大小
        self.mic_button.setStyleSheet(
            "background-color: white; border: 1px solid black; border-radius: 5px;"
        )  # 初始状态白色背景
        self.mic_button.setText("🎤")  # 设置初始图标
        self.mic_button.clicked.connect(self.toggle_recording)

        # 创建识别线程
        self.recognition_thread = RecognitionThread(self.recognizer)
        self.recognizer.recording_ended_signal.connect(self.on_recognition_complete)
        self.recognizer.detect_speech_signal.connect(self.detect_speech_toggle)

        # 设置语音识别中标志, 该标志传递给ui模块以控制对话框文本输出
        self.recognizer_is_updating = False
        # 按钮状态, 初始化按钮状态为没有按下
        self.mic_button_pressed_state = False

    def toggle_recording(self):
        """点击语音识别按钮"""
        logger.debug("触发了toggle_recording")
        if self.mic_button_pressed_state:  # 当按钮已经被按下
            if self.recognizer._is_running:
                self.recognition_thread.stop()  # 如果语音识别正在进行，停止线程
            self.set_button_color("white")  # 关闭录音, 按钮白色
            self.mic_button_pressed_state = False  # 按钮恢复为没有按下
        else:
            if not self.recognizer._is_running:
                self.recognition_thread.start()  # 启动识别线程
            self.set_button_color("gray")  # 开启录音, 按钮灰色
            self.mic_button_pressed_state = True  # 按钮更新为已经按下

    def on_recognition_complete(self):
        """语音识别结束操作"""
        self.recognizer_is_updating = False  # 识别完成, 重置标志
        self.set_button_color("red")  # 切换按钮图标颜色
        if self.recognizer._is_running:
            self.recognition_thread.stop()  # 如果语音识别正在进行，停止线程
        logger.info("识别完成，停止录音")

    def set_button_color(self, color):
        """设置语音识别按钮颜色

        Args:
            color (str): 按钮颜色名称 (英文)
        """
        self.mic_button.setText("🎤")
        self.mic_button.setStyleSheet(
            f"background-color: {color}; border: 1px solid black; border-radius: 5px;"
        )

    def detect_speech_toggle(self, flag=False):
        """当检测到人声输入时的行为

        Args:
            flag (bool, optional): 按钮是否已经按下的标记. Defaults to False.
        """
        if flag:
            self.set_button_color("green")
            self.recognizer.vits_speaker.vits_stop_audio()
        else:
            self.set_button_color("gray")


# 启动应用
if __name__ == "__main__":
    import logging_config, yaml

    # 初始化日志配置
    logging_config.setup_logging()
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    app = QApplication(sys.argv)
    window = MicButton(settings)
    window.show()
    sys.exit(app.exec_())
