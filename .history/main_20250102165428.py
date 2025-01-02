import sys
import json
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication
from ui_module import TachieDisplay  # 假设TachieDisplay在tachie_display.py中
from model_module import Model  # 导入模型类
from replyParser_module import replyParser  # 导入回复内容解析器


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
        self.app = QApplication(sys.argv)
        self.window = TachieDisplay()
        self.chat_model = Model()  # 初始化模型实例
        self.setup_ui()
        self.typing_animation_timer = QTimer()
        self.typing_dots = ""

    def setup_ui(self):
        self.window.display_text(
            "你好，我是远山绫！有什么可以帮忙的吗？", is_non_user_input=True
        )
        self.window.text_sent.connect(self.on_text_received)
        self.window.show()

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
                final_message = self.process_response(
                    str(parsed_arguments.get("message", "没有消息内容"))
                )
            except json.JSONDecodeError:
                final_message = "无法解析消息"
        else:
            final_message = "没有有效的回复"

        self.window.display_text(final_message, is_non_user_input=True)

    def process_response(self, msg):
        parsed_reply = replyParser(msg)
        parse_status = parsed_reply.get("status")
        parse_message = parsed_reply.get("message")

        Chinese_message = parse_message

        if not parse_status:
            tachie_expression = parsed_reply.get("data").get("ep")
            Chinese_message = parsed_reply.get("data").get("zh")
            Japanese_message = parsed_reply.get("data").get("jp")
            print("tachie_expression:", tachie_expression)
            print("Chinese_message:", Chinese_message)
            print("Japanese_message:", Japanese_message)

        return Chinese_message

    def run(self):
        sys.exit(self.app.exec_())


# if __name__ == "__main__":
#     main_app = MainApp()
#     main_app.run()

DEBUG = True

if DEBUG:
    main_app = MainApp()
    main_app.on_model_response("""
                               {
    "messages": [
        {
            "id": "message-f94292ad-3ec4-4d8b-9178-f23f2a8eaac6",
            "date": "2025-01-02T08:45:22+00:00",
            "message_type": "reasoning_message",
            "reasoning": "User is interested in news related to Hatsune Miku concerts. I will search for the latest updates."
        },
        {
            "id": "message-f94292ad-3ec4-4d8b-9178-f23f2a8eaac6",
            "date": "2025-01-02T08:45:22+00:00",
            "message_type": "tool_call_message",
            "tool_call": {
                "name": "internet_search",
                "arguments": "{\n  \"query\": \"Hatsune Miku concert news January 2025\",\n  \"region\": \"us-en\",\n  \"search_type\": \"news\",\n  \"max_results\": 5,\n  \"request_heartbeat\": true\n}",
                "tool_call_id": "call_eoCs0ePWFIHMo8N3KSmJJpDC"
            }
        },
        {
            "id": "message-33640b3b-08ad-4cba-a096-9735327194bc",
            "date": "2025-01-02T08:45:24+00:00",
            "message_type": "tool_return_message",
            "tool_return": "[{'date': '2012-07-07T08:59:00+00:00', 'title': 'Hatsune Miku (Concert)', 'body': 'Big news, my fellow otaku. Mega virtual J-pop idol, Miku Hatsune, will be coming to Hong Kong for a special live concert. The Hatsune Miku Hong Kong & Taiwan First Concert \"MIKUPA\" will take place ...', 'url': 'https://www.scmp.com/yp/discover/lifestyle/features/article/3062723/hatsune-miku-concert', 'image': '', 'source': 'scmp.com'}, {'date': '2024-12-09T14:00:00+00:00', 'title': 'Icon Hatsune Miku is Coming to Fortnite', 'body': 'Hatsune Miku may simply be a purchasable skin, but she could also be the center of a Battle Pass. Hopefully, there will be a concert or live ... as a skin and boss in January.', 'url': 'https://www.msn.com/en-us/travel/news/icon-hatsune-miku-is-coming-to-fortnite/ar-AA1vxgAX', 'image': '', 'source': 'MSN'}, {'date': '2024-12-28T23:59:00+00:00', 'title': \"Man finds bliss after 'marrying' virtual idol Hatsune Miku\", 'body': 'He saw a psychiatrist and took sick leave. Around that time, he came across Hatsune Miku and started attending fan events and concerts. \"She was a savior. My mind recovered while I cried or was ...', 'url': 'https://www.asahi.com/ajw/articles/14893578', 'image': '', 'source': '朝日新聞社'}, {'date': '2024-12-08T23:59:00+00:00', 'title': 'Fortnite Hatsune Miku crossover coming, leaks suggest', 'body': 'And yet, despite not existing IRL, Hatsune Miku is something of a cultural icon: the voice of hundreds of thousands of songs, star of virtual concerts, and playable in several video games.', 'url': 'https://www.eurogamer.net/fortnite-hatsune-miku-crossover-coming-leaks-suggest', 'image': '', 'source': 'Eurogamer'}, {'date': '2023-09-02T17:15:00+00:00', 'title': 'Synthesized singing sensation Hatsune Miku turns sweet 16', 'body': 'The voice synthesizer software has been featured in more than 100,000 songs, performed in 3D concerts in Los Angeles and Hong Kong, and inspired countless works of art. Hatsune Miku owes her reign ...', 'url': 'https://www.asahi.com/ajw/articles/14996084', 'image': '', 'source': '朝日新聞社'}]",
            "status": "success",
            "tool_call_id": "call_eoCs0ePWFIHMo8N3KSmJJpDC",
            "stdout": null,
            "stderr": null
        },
        {
            "id": "message-9c455ee0-b6ee-42a6-b92f-e022d8f0e226",
            "date": "2025-01-02T08:45:32+00:00",
            "message_type": "reasoning_message",
            "reasoning": "User asked for news about Hatsune Miku concerts. I’ve gathered the latest relevant information and shared it."
        },
        {
            "id": "message-9c455ee0-b6ee-42a6-b92f-e022d8f0e226",
            "date": "2025-01-02T08:45:32+00:00",
            "message_type": "tool_call_message",
            "tool_call": {
                "name": "send_message",
                "arguments": "{\n  \"message\": \"好奇 ||| 关于初音的最新演唱会新闻：\\n1. **初音未来即将在Fortnite中登场** - 她可能不仅是可购买的皮肤，还可 能成为战斗通行证的中心角色。希望在1月会有演唱会或现场活动，值得期待。[查看详细信息                ](https: //www.msn.com/en-us/travel/news/icon-hatsune-miku-is-coming-to-fortnite/ar-AA1vxgAX)\\n2. **一名男性与虚拟偶像初音未来的“结婚”故事** - 从他的经历中可以看到，初音未来在他的生活中有着重要的地位，参加演唱会和粉丝活动让他感到幸福。[查看详细信息                ](https: //www.asahi.com/ajw/articles/14893578)\\n3. **Fortnite与初音未来的互动跨界即将推出** - 虽然初音未来在现实中并不存在，但她已成为一种 文化符号，拥有数以万计的歌声和虚拟演唱会。[查看详细信息                ](https: //www.eurogamer.net/fortnite-hatsune-miku-crossover-coming-leaks-suggest)\\n希望这些信息对您了解初音未来的演唱会情况有所帮助！||| 初音未来についての最新のコンサートニュース：\\n1. **初音ミクがFortniteに登場予定** - 彼女は単なる購入可能なスキンだけでなく、バトルパスの中心人物になる可能性があります。1月にはコンサートやライブイベントが開催されることを期待しています。[詳細情報はこちら               ](https: //www.msn.com/en-us/travel/news/icon-hatsune-miku-is-coming-to-fortnite/ar-AA1vxgAX)\\n2. **男性が虚構のアイドル初音ミクと「結婚」した話** - 彼の体験から、初音ミクが彼の生活で重要な役割を果たしていることがわかります。コンサートやファンイベントに参加することは彼に幸せをもたらしました。[詳細情報はこちら                ](https: //www.asahi.com/ajw/articles/14893578)\\n3. **Fortniteと初音ミクのコラボが近づいています** - 初音ミクは現実には存在しませんが、数万曲の声と仮想コンサートで文化のアイコンとなっ ています。[詳細情報はこちら                ](https: //www.eurogamer.net/fortnite-hatsune-miku-crossover-coming-leaks-suggest)\\nこれらの情報が初音ミクのコンサートに関する理解に役立つことを願っています！\"\n}",
                "tool_call_id": "call_7njp4sLyUMmUdyu8UHZithVI"
            }
        },
        {
            "id": "message-47af5eba-065b-491d-8c9c-3da0fb3a62eb",
            "date": "2025-01-02T08:45:32+00:00",
            "message_type": "tool_return_message",
            "tool_return": "None",
            "status": "success",
            "tool_call_id": "call_7njp4sLyUMmUdyu8UHZithVI",
            "stdout": null,
            "stderr": null
        }
    ],
    "usage": {
        "completion_tokens": 709,
        "prompt_tokens": 29733,
        "total_tokens": 30442,
        "step_count": 2
    }
}""")