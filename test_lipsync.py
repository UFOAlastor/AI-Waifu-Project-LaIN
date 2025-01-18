from PyQt5.QtWidgets import QApplication
from live2d_module import Live2DApp
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
    main_window = Live2DApp(settings)
    main_window.show()

    def test_lipsync(mouth_open_y):
        main_window.set_mouth_open_y(mouth_open_y)

    vits_speaker = vitsSpeaker(settings)

    vits_speaker.audio_lipsync_signal.connect(test_lipsync)

    # 要合成的日语文本
    text = "今日はとても楽しい一日だったよ～！シアロ～(∠・ω< )⌒☆ 何か面白いことがあったら教えてね！"

    # 调用合成并播放的功能
    vits_speaker.vits_play(text)

    sys.exit(app.exec_())
