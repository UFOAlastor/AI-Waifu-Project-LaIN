import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget
from PyQt5.QtCore import QTimer
from OpenGL.GL import *
from OpenGL.GLUT import *
import live2d.v3 as live2d
from live2d.v3 import StandardParams
from lipsync_module import WavHandler
import logging

# 获取根记录器
logger = logging.getLogger("live2d_module")


class Live2DWidget(QOpenGLWidget):
    def __init__(self, parent, main_settings):
        super().__init__(parent)
        self.model = None
        # 获取配置文件信息
        self.model_path = main_settings.get(
            "live2d_model_path", "./live2d/MuraSame/Murasame.model3.json"
        )
        self.lipSyncN = main_settings.get("live2d_lipSyncN", 5)
        # 初始化响度检测模块
        self.wavHandler = WavHandler()
        self.mouth_open_y = 0.0
        # 配置显示刷新
        self.update_scene_timer = QTimer(self)  # 定时器
        self.update_scene_timer.timeout.connect(self.update_scene)
        self.update_scene_timer.start(16)  # 每16毫秒刷新一次（60帧）
        # 配置Idle动作刷新
        self.update_motionIdle_timer = QTimer(self)
        self.update_motionIdle_timer.timeout.connect(self.update_motionIdle)
        self.update_motionIdle_timer.start(6000) # 眨眼频率

    def initializeGL(self):
        """初始化 OpenGL 和 Live2D"""
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)  # 启用深度测试
        glEnable(GL_BLEND)  # 启用透明度混合
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # 设置混合模式

        # 初始化 Live2D
        live2d.glewInit()
        live2d.init()

        # 加载 Live2D 模型
        self.model = live2d.LAppModel()
        self.model.LoadModelJson(self.model_path)

        self.model.Resize(self.width(), self.height())
        self.model.Update()

        logger.debug("模型加载完成")

        # 获取全部可用参数
        for i in range(self.model.GetParameterCount()):
            param = self.model.GetParameter(i)
            print(
                param.id, param.type, param.value, param.max, param.min, param.default
            )

    def resizeGL(self, w, h):
        """调整窗口大小"""
        glViewport(0, 0, w, h)
        if self.model:
            self.model.Resize(w, h)

    def paintGL(self):
        """绘制模型"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # 清空颜色和深度缓冲
        if self.model:
            self.model.Update()  # 更新模型
            self.model.SetParameterValue(
                StandardParams.ParamMouthOpenY,
                self.mouth_open_y * self.lipSyncN,
                1.0,
            )
            self.model.Draw()  # 绘制模型

    def set_mouth_open_y(self, mouth_open_y):
        mouth_open_y = max(0, mouth_open_y)
        mouth_open_y = min(1, mouth_open_y)
        self.mouth_open_y = mouth_open_y

    def update_motionIdle(self):
        self.model.StartRandomMotion("Idle", 1, None, None)

    def update_scene(self):
        """更新场景"""
        self.update()


class Live2DApp(QMainWindow):
    def __init__(self, main_settings):
        super().__init__()
        self.setWindowTitle("Live2D PyQt 示例")
        self.setGeometry(100, 100, 600, 800)

        logger.debug("显示live2d")

        # 添加 Live2DWidget 到主窗口
        self.live2d_widget = Live2DWidget(self, main_settings)
        self.setCentralWidget(self.live2d_widget)

    def set_mouth_open_y(self, mouth_open_y):
        self.live2d_widget.set_mouth_open_y(mouth_open_y)


if __name__ == "__main__":
    import logging_config, yaml

    # 初始化日志配置
    logging_config.setup_logging()
    # 加载配置文件
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    app = QApplication(sys.argv)
    main_window = Live2DApp(settings)
    main_window.show()
    sys.exit(app.exec_())
