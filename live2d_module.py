import sys
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import QTimer, Qt
from OpenGL.GL import *
from OpenGL.GLUT import *
import live2d.v3 as live2d
from live2d.v3 import StandardParams
from lipsync_module import WavHandler
import logging

# 获取根记录器
logger = logging.getLogger("live2d_module")


class Live2DWidget(QOpenGLWidget):
    def __init__(self, main_settings, parent=None):
        super().__init__(parent)
        self.model = None
        # 获取配置文件信息
        self.model_path = main_settings.get(
            "live2d_model_path", "./live2d/MuraSame/Murasame.model3.json"
        )
        self.lipSyncN = main_settings.get("live2d_lipSyncN", 5)
        # 设置透明背景
        self.setAutoFillBackground(False)  # 禁止Qt自动填充背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 初始化响度检测模块
        self.wavHandler = WavHandler()
        self.mouth_open_y = 0.0
        # 配置显示刷新
        self.update_scene_timer = QTimer(self)  # 定时器
        self.update_scene_timer.timeout.connect(self.update_scene)
        self.update_scene_timer.start(16)  # 每16毫秒刷新一次（60帧）

        QTimer.singleShot(500, lambda: self.play_motion("高兴wink"))
        QTimer.singleShot(4500, lambda: self.play_motion("好奇地探身"))
        QTimer.singleShot(9000, lambda: self.play_motion("Idle"))

    def initializeGL(self):
        """初始化 OpenGL 和 Live2D"""
        glEnable(GL_DEPTH_TEST)  # 启用深度测试
        glEnable(GL_BLEND)  # 启用透明度混合
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # 设置混合模式
        glClearColor(0, 0, 0, 0)  # 设置透明背景

        # 初始化 Live2D
        live2d.glewInit()
        live2d.init()

        # 加载 Live2D 模型
        self.model = live2d.LAppModel()
        self.model.LoadModelJson(self.model_path)
        self.model.Resize(self.width(), self.height())
        self.model.Update()

        logger.debug("模型加载完成")

    def resizeGL(self, w, h):
        """调整窗口大小"""
        glViewport(0, 0, w, h)
        if self.model:
            self.model.Resize(w, h)

    def paintGL(self):
        """绘制模型"""
        glClearColor(0, 0, 0, 0)  # 强制设置透明背景
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # 清除颜色缓冲并设置透明背景
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

    def play_motion(self, motion_name):
        if self.model is None:
            logger.warning("Model not loaded properly")
            return
        self.model.StartMotion(motion_name, 0, live2d.MotionPriority.FORCE)

    def play_expression(self, exp_name):
        if self.model is None:
            logger.warning("Model not loaded properly")
            return
        self.model.SetExpression(exp_name)

    def update_scene(self):
        """更新场景"""
        self.update()


if __name__ == "__main__":
    import logging_config, yaml

    # 初始化日志配置
    logging_config.setup_logging()
    # 加载配置文件
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    app = QApplication(sys.argv)
    main_window = Live2DWidget(settings)
    main_window.show()
    sys.exit(app.exec_())
