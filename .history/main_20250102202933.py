import sys
import json
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication
from ui_module import TachieDisplay  # 假设TachieDisplay在tachie_display.py中
from model_module import Model  # 导入模型类
from replyParser_module import replyParser  # 导入回复内容解析器
from vits_module import vitsSpeaker


class ChatModelWorker(QThread):
    """用于后台运行模型的线程"""

    response_ready = pyqtSignal(dict)

    def __init__(self, model, input_text):
        super().__init__()
        self.model = model
        self.input_text = input_text

    def run(self):
        try:
            response = self.model.get_response(self.input_text)
            self.response_ready.emit(response)
        except Exception as e:
            print(f"Error in model worker: {e}")
            self.response_ready.emit({"error": str(e)})


class MainApp:
    def __init__(self):
        self.settings = self.load_settings("./config.json")  # 默认加载路径为 "./config.json"
        self.app = QApplication(sys.argv)
        self.window = TachieDisplay(self.settings)  # 初始化图形界面实例
        self.chat_model = Model(self.settings)  # 初始化语言模型实例
        self.setup_ui()
        self.typing_animation_timer = QTimer()
        self.typing_dots = ""
        vitsSpeaker.set_settings(self.settings)  # vits语音模块加载配置文件

    def load_settings(file_path="./config.json"):
        """加载配置文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings
        except FileNotFoundError:
            print(f"未找到设置文件: {file_path}")
        except json.JSONDecodeError:
            print(f"设置文件格式错误: {file_path}")
        return {}

    def setup_ui(self):
        self.window.display_text(
            "Ciallo～(∠・ω< )⌒☆ 我是绫！有什么能帮忙的吗?", is_non_user_input=True
        )
        self.window.text_sent.connect(self.on_text_received)
        self.window.show()
        vitsSpeaker.vits_play(
            "チャロ！わが輩はレイだよ！何かお手伝いできること、あるかな～？"
        )

    def on_text_received(self, input_text):
        """等待接收模型回复"""
        if input_text:
            # 显示动态省略号动画
            self.start_typing_animation()

            # 启动后台线程调用模型
            self.worker = ChatModelWorker(self.chat_model, input_text)
            self.worker.response_ready.connect(self.on_model_response)
            self.worker.start()

    def start_typing_animation(self):
        """启动动态省略号动画"""
        self.typing_dots = ""
        self.window.display_text("绫正在思考中", is_non_user_input=True)
        self.typing_animation_timer.timeout.connect(self.update_typing_animation)
        self.typing_animation_timer.start(4000)  # 每隔 4000ms 更新一次

    def update_typing_animation(self):
        """更新动态省略号"""
        if len(self.typing_dots) < 3:
            self.typing_dots += "。"
        else:
            self.typing_dots = ""
        self.window.display_text(
            f"绫正在思考中{self.typing_dots}", is_non_user_input=True
        )

    def stop_typing_animation(self):
        """停止动态省略号动画"""
        self.typing_animation_timer.stop()
        self.typing_animation_timer.timeout.disconnect(self.update_typing_animation)

    def on_model_response(self, response):  # ATTENTION 关键的模型回复处理部分
        """处理模型的回复"""
        # 停止动态省略号动画
        self.stop_typing_animation()

        if "error" in response:
            self.window.display_text(
                "对不起，发生了错误。请稍后再试。", is_non_user_input=True
            )
            return

        # 查找第一个包含 'tool_call_message' 且 name = 'send_message' 类型的消息
        tool_call_message = next(
            (
                msg
                for msg in response.get("messages", [])
                if msg.get("message_type") == "tool_call_message"
                and msg.get("tool_call", {}).get("name") == "send_message"
            ),
            None,
        )

        if tool_call_message:
            reply_text = tool_call_message.get("tool_call", {}).get("arguments", "")
            try:
                parsed_arguments = json.loads(reply_text)
                final_message = self.parse_response(
                    str(parsed_arguments.get("message", "没有消息内容"))
                )
            except json.JSONDecodeError:
                final_message = "无法解析消息"
        else:
            final_message = "没有有效的回复"

        self.window.display_text(final_message, is_non_user_input=True)

    def parse_response(self, msg):
        """对模型回复{表情}|||{中文}|||{日语}进行解析"""
        parsed_reply = replyParser(msg)
        parse_status = parsed_reply.get("status")
        parse_message = parsed_reply.get("message")

        # 默认对话框展示中文, 其中parse_message可能包含解析时错误提示
        Chinese_message = parse_message

        if not parse_status:
            tachie_expression = parsed_reply.get("data").get("ep")
            Chinese_message = parsed_reply.get("data").get("zh")
            Japanese_message = parsed_reply.get("data").get("jp")
            print("tachie_expression:", tachie_expression)
            print("Chinese_message:", Chinese_message)
            print("Japanese_message:", Japanese_message)

        # 处理立绘切换
        self.change_tachie(tachie_expression)

        # 播放语音, 默认日语
        vitsSpeaker.vits_play(Japanese_message)

        return Chinese_message

    def change_tachie(self, tachie_name):
        """立绘切换"""
        # 展示指定的立绘
        self.window.tachie_display(tachie_name)
        print("切换立绘:", tachie_name)

        # 设置6秒后执行回调函数，切换回默认立绘
        QTimer.singleShot(
            6000, lambda: self.window.tachie_display(self.window.default_tachie)
        )

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
