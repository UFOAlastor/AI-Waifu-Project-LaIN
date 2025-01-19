from PyQt5.QtWidgets import QApplication
from live2d_module import Live2DWidget
from vits_module import vitsSpeaker


# 测试生成和播放音频
if __name__ == "__main__":
    import logging_config, yaml, sys

    # 初始化日志配置
    logging_config.setup_logging()
    # 加载配置文件
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    app = QApplication(sys.argv)
    main_window = Live2DWidget(settings)
    main_window.show()

    vits_speaker = vitsSpeaker(settings)
    vits_speaker.audio_lipsync_signal.connect(main_window.set_mouth_open_y)

    # 要合成的日语文本
    text = "チャロ！わが輩はレイだよ！何かお手伝いできること、あるかな～？"

    # 调用合成并播放的功能
    vits_speaker.vits_play(text)

    sys.exit(app.exec_())
