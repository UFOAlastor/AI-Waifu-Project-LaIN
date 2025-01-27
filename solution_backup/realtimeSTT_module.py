import threading
from PyQt5.QtCore import QObject, pyqtSignal
from RealtimeSTT import AudioToTextRecorder


class STTController(QObject):
    transcription_completed = pyqtSignal(str)
    realtime_transcription_update = pyqtSignal(str)
    voice_detected = pyqtSignal()

    def __init__(
        self,
        model_size="base",
        enable_realtime=False,
        realtime_model_type="tiny",
        language="zh",
        parent=None,
    ):
        super().__init__(parent)
        self.is_running = False
        self.recorder = None
        self.lock = threading.Lock()
        # 持久化配置参数
        self.model_size = model_size
        self.enable_realtime = enable_realtime
        self.realtime_model_type = realtime_model_type
        self.language = language
        # 初始化录音器（仅创建一次）
        self._init_recorder()

    def _init_recorder(self):
        """初始化并配置录音器（包含语言设置）"""
        with self.lock:
            self.recorder = AudioToTextRecorder(
                model=self.model_size,
                language=self.language,  # 添加语言配置
                enable_realtime_transcription=self.enable_realtime,
                realtime_model_type=self.realtime_model_type,
                on_recording_start=self._on_recording_start,
                on_recording_stop=self._on_recording_stop,
                on_realtime_transcription_update=self._on_realtime_update,
                post_speech_silence_duration=0.4,
                silero_sensitivity=0.5,
                webrtc_sensitivity=3,
                use_microphone=True,
                min_gap_between_recordings=0.3,
                handle_buffer_overflow=True,
                compute_type="int8",
                realtime_processing_pause=0.1,
                beam_size=7,
                beam_size_realtime=3,
                debug_mode=False,
            )

    def start(self):
        """启动持续监听"""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """安全停止监听"""
        with self.lock:
            if not self.is_running:
                return
            self.is_running = False
            if self.recorder:
                self.recorder.stop()
                self.recorder.shutdown()

    def _processing_loop(self):
        """优化后的处理循环"""
        try:
            while self.is_running:
                # 使用持久化的录音器实例
                with self.lock:
                    if not self.recorder:
                        self._init_recorder()
                    text = self.recorder.text().strip()
                    if text:
                        self.transcription_completed.emit(text)
                # 降低CPU占用
                threading.Event().wait(0.1)
        except Exception as e:
            print(f"Processing error: {e}")
        finally:
            self._cleanup()

    def _cleanup(self):
        """资源清理"""
        with self.lock:
            if self.recorder:
                self.recorder.shutdown()
                self.recorder = None

    def _on_recording_start(self):
        """语音活动开始回调"""
        if self.is_running:
            self.voice_detected.emit()

    def _on_recording_stop(self):
        """录音结束回调"""
        pass

    def _on_realtime_update(self, text):
        """实时更新处理"""
        if self.is_running:
            self.realtime_transcription_update.emit(text.strip())


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    controller = STTController(
        model_size="large-v3-turbo",
        enable_realtime=False,
        realtime_model_type="tiny",
        language="zh",  # 指定中文
    )

    controller.transcription_completed.connect(
        lambda text: print(f"\n最终转录: {text}")
    )
    controller.realtime_transcription_update.connect(
        lambda text: print(f"实时更新: {text}", end="\r")
    )
    controller.voice_detected.connect(lambda: print("\n检测到人声..."))

    controller.start()
    input("Press Enter to stop...")
    controller.stop()

    sys.exit(app.exec_())
