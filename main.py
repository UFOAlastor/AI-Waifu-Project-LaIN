# main.py

import sys, yaml
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication
from replyParser_module import replyParser  # 导入回复内容解析器
import logging, logging_config
from logging_config import gcww

# 初始化日志配置
logging_config.setup_logging()
# 获取根记录器
logger = logging.getLogger()

# 导入模块类
from ui_module import UIDisplay  # 界面
from lettaModel_module import LettaModel  # letta框架
from functioncall_module import FunctioncallManager  # 带函数调用的模型框架
from mem0_module import memModule  # 记忆模块


class ChatModelWorker(QThread):
    """用于后台运行模型的线程"""

    response_ready = pyqtSignal(object)

    def __init__(self, model, mem_module, user_name, input_text):
        super().__init__()
        self.model = model
        self.mem_module = mem_module
        self.user_name = user_name
        self.input_text = input_text

    def run(self):
        try:
            if self.mem_module != None:  # 仅当mem0模块对象存在时才处理传入文本
                self.input_text = (  # 相关记忆召回
                    self.mem_module.recall_mem(self.user_name, self.input_text)
                    + self.input_text
                )
            response = self.model.get_response(self.user_name, self.input_text)
            logger.debug(f"rsp: {response}")
            self.response_ready.emit(response)
        except Exception as e:
            logger.error(f"Error in model worker: {e}")
            self.response_ready.emit({"error": str(e)})


class MemoryRecordWorker(QThread):
    """记忆记录非阻塞实现"""

    def __init__(self, mem_module, message):
        super().__init__()
        self.mem_module = mem_module
        self.message = message

    def run(self):
        self.mem_module.record_mem(self.message)


def load_settings(file_path="./config.yaml"):
    """加载配置文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            settings = yaml.safe_load(f)
            return settings
    except FileNotFoundError:
        logger.error(f"未找到设置文件: {file_path}")
    except yaml.YAMLError as e:
        logger.error(f"设置文件格式错误: {file_path}. 错误详情: {e}")
    return {}


class MainApp:
    # 系统函数
    def register_voiceprint(self, user_name):
        logger.debug(f"进行用户{user_name}的声纹注册")
        self.window.recognizer.vpr_manager.register_voiceprint(
            self._tmp_audio_frames, user_name
        )

    SYSTEM_FUNC_DESC = [
        {
            "name": "register_voiceprint",
            "description": "注册当前对话者的声纹样本",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_name": {
                        "type": "string",
                        "description": "注册用户名称",
                    },
                },
                "required": ["user_name"],
            },
        }
    ]

    def __init__(self):
        # 加载配置文件
        self.settings = load_settings()  # 默认加载路径为 "./config.yaml"
        # UI界面初始化
        self.app = QApplication(sys.argv)
        self.window = UIDisplay(self.settings)  # 初始化图形界面实例
        # 模型框架选取
        self.model_frame_type = gcww(self.settings, "model_frame_type", "letta", logger)
        if self.model_frame_type == "letta":
            # letta框架自带Function功能, 无需额外加载FunctioncallManager
            self.chat_model = LettaModel(self.settings)
        elif self.model_frame_type == "ollama" or self.model_frame_type == "openaiType":
            # 使用FunctioncallManager实现函数调用
            self.chat_model = FunctioncallManager(self.settings)
            # 设置用户音频缓存
            self._tmp_audio_frames = []
            # 注册系统函数
            self.register_system_funcall()
        # 记忆框架初始化
        self.mem_module_open = gcww(self.settings, "mem0_switch", True, logger)
        if self.mem_module_open:  # 仅当开启mem0模块时才创建该对象
            self.mem_module = memModule(self.settings)
        # "思考中..."动态效果初始化
        self.typing_animation_timer = QTimer()
        self.typing_dots = ""
        # 显示UI界面
        self.setup_ui()
        # vitsSpeaker连接槽
        self.window.recognizer.vits_speaker.audio_start_play.connect(
            self.start_voice_rec
        )
        # 针对live2d显示模式绑定口型同步信号
        if self.window.character_display_mode == "live2d":
            self.window.recognizer.vits_speaker.audio_lipsync_signal.connect(
                self.window.live2d_widget.set_mouth_open_y
            )

    def setup_ui(self):
        """显示初始化内容 (提示词, 开场语音)"""
        self.window.display_text(
            "Ciallo～(∠・ω< )⌒☆ 我是绫！有什么能帮忙的吗?", is_non_user_input=True
        )
        self.window.text_sent_signal.connect(self.on_text_received)
        self.window.show()
        self.window.recognizer.vits_speaker.vits_play(
            "チャロ！わが輩はレイだよ！何かお手伝いできること、あるかな～？"
        )
        # 开场角色立绘/动作表情显示
        if self.window.character_display_mode == "tachie":
            self.window.character_display(self.window.tachie_opening)
            QTimer.singleShot(
                3600, lambda: self.window.character_display(self.window.tachie_default)
            )
        elif self.window.character_display_mode == "live2d":
            QTimer.singleShot(
                100,
                lambda: self.window.character_display(
                    self.window.live2d_opening_expression
                ),
            )
            QTimer.singleShot(
                100,
                lambda: self.window.character_display(
                    self.window.live2d_opening_motion
                ),
            )
            QTimer.singleShot(
                4700,
                lambda: self.window.character_display(
                    self.window.live2d_default_expression
                ),
            )
            QTimer.singleShot(
                4700,
                lambda: self.window.character_display(
                    self.window.live2d_default_motion
                ),
            )

    def register_system_funcall(self):
        """注册系统函数调用"""

        self.chat_model.register_func_desc(self.SYSTEM_FUNC_DESC)
        self.chat_model.register_func_impl(
            "register_voiceprint", self.register_voiceprint
        )
        self.chat_model.show_registered_functions()

    def start_voice_rec(self):
        """继续开启语音识别"""
        if self.window.mic_button_pressed_state:
            # 当语音识别按钮处于被按下状态, 这时允许重新启动语音识别
            if not self.window.recognizer._is_running:
                self.window.recognition_thread.start()  # 启动识别线程
            self.window.set_button_color("gray")  # 开启录音, 按钮灰色
            logger.debug("语音播放结束, 自动重启语音识别")

    def on_text_received(self, tuple_data):
        """等待接收模型回复

        Args:
            tuple_data (tuple): 输入给模型的三元对, 内容为(user_name, audio_frames, input_text)
        """
        user_name, self._tmp_audio_frames, input_text = tuple_data

        if input_text:
            # 显示动态省略号动画
            self.start_typing_animation()

            # 实现自然的声纹注册
            if user_name == "Unknown":
                logger.debug("声纹未匹配到用户: Unknown")
                input_text = (
                    "[用户声纹未注册, 如果用户没有表明身份, 请引导用户说出身份以完成注册; 如果用户已经表明身份, 应该立刻提取出用户名称并调用register_voiceprint函数进行注册, 无需和用户进行确认]\n\n"
                    + input_text
                )

            # 启动后台线程调用模型
            if self.mem_module_open:
                self.worker = ChatModelWorker(
                    self.chat_model, self.mem_module, user_name, input_text
                )
            else:  # 没有启用mem0模块, 传入None
                self.worker = ChatModelWorker(
                    self.chat_model, None, user_name, input_text
                )
            self.worker.response_ready.connect(self.on_model_response)
            self.worker.start()

    def start_typing_animation(self):
        """启动动态省略号动画"""
        self.typing_dots = ""
        self.window.display_text("绫正在思考中", is_non_user_input=True)
        self.typing_animation_timer.timeout.connect(self.update_typing_animation)
        self.typing_animation_timer.start(3600)  # 更新频率

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

    def on_model_response(self, response):  # ATTENTION 模型回复处理部分
        """处理模型的回复, 解析提取出有效内容

        Args:
            response (str): 模型原始回复内容
        """
        self.stop_typing_animation()  # 停止动态省略号动画
        final_message = self.parse_response(response)
        self.window.display_text(final_message, is_non_user_input=True)
        if self.mem_module_open:  # 判断是否开启mem0模块
            # 非阻塞的记忆记录
            self.mem_record_worker = MemoryRecordWorker(self.mem_module, final_message)
            self.mem_record_worker.start()

    def parse_response(self, msg):
        """对模型回复{表情}|||{中文}|||{日语}进行解析

        Args:
            msg (str): 模型原始回复

        Returns:
            str: 中文回复文本
        """
        parsed_reply = replyParser(msg)
        parse_status = parsed_reply.get("status")
        parse_message = parsed_reply.get("message")

        # 默认对话框展示中文, 其中parse_message可能包含解析时错误提示
        Chinese_message = parse_message

        if not parse_status:
            tachie_expression = parsed_reply.get("data").get("ep")
            Chinese_message = parsed_reply.get("data").get("zh")
            Japanese_message = parsed_reply.get("data").get("jp")
            logger.debug(f"tachie_expression: {tachie_expression}")
            logger.debug(f"Chinese_message: {Chinese_message}")
            logger.debug(f"Japanese_message: {Japanese_message}")

            # 处理角色表情切换
            self.change_emotion(tachie_expression)

            # 播放语音, 默认日语
            self.window.recognizer.vits_speaker.vits_play(Japanese_message)

        return Chinese_message

    def change_emotion(self, emotion_name):
        """角色情绪切换

        Args:
            emotion_name (str): 情绪名称 (表情/动作名称)
        """
        self.window.character_display(emotion_name)  # 展示指定的表情
        logger.debug(f"切换角色情绪: {emotion_name}")

        if self.window.character_display_mode == "tachie":
            # 设置5.5秒后执行回调函数，切换回默认表情
            QTimer.singleShot(
                5500, lambda: self.window.character_display(self.window.tachie_default)
            )
        elif self.window.character_display_mode == "live2d":
            # 设置6秒后执行回调函数，切换回默认表情和动作
            QTimer.singleShot(
                5500,
                lambda: self.window.character_display(
                    self.window.live2d_default_expression
                ),
            )
            QTimer.singleShot(
                5500,
                lambda: self.window.character_display(
                    self.window.live2d_default_motion
                ),
            )

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
