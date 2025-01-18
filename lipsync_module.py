# lipsynv_module.py
# 音频响度检测实现口型同步, 源代码见live2d-py仓库: https://github.com/Arkueid/live2d-py/blob/main/package/live2d/utils/lipsync.py

import wave
import time
import numpy as np
from io import BytesIO
import logging

# 获取根记录器
logger = logging.getLogger("lipsync_module")


class WavHandler:
    def __init__(self):
        # 每个通道的采样帧数
        self.numFrames: int = 0
        # 采样率，帧/秒
        self.sampleRate: int = 0
        self.sampleWidth: int = 0
        # 通道数
        self.numChannels: int = 0
        # 数据
        self.pcmData: np.ndarray = None
        # 已经读取的帧数
        self.lastOffset: int = 0
        # 当前rms值
        self.currentRms: float = 0
        # 开始读取的时间
        self.startTime: float = -1

    def Start(self, audio_data: bytes) -> None:
        """接收并处理音频数据"""
        self.ReleasePcmData()
        try:
            audio_stream = BytesIO(audio_data)
            with wave.open(audio_stream, "rb") as wav:
                self.numFrames = wav.getnframes()
                self.sampleRate = wav.getframerate()
                self.sampleWidth = wav.getsampwidth()
                self.numChannels = wav.getnchannels()
                self.pcmData = np.frombuffer(
                    wav.readframes(self.numFrames), dtype=np.int16
                )
                self.pcmData = self.pcmData / np.max(np.abs(self.pcmData))
                self.pcmData = self.pcmData.reshape(-1, self.numChannels).T
                self.startTime = time.time()
                self.lastOffset = 0
        except Exception as e:
            self.ReleasePcmData()
            logger.error(f"音频数据加载失败: {e}")

    def ReleasePcmData(self):
        if self.pcmData is not None:
            del self.pcmData
            self.pcmData = None

    def GetRms(self) -> float:
        return self.currentRms

    def Update(self) -> bool:
        """更新音频帧位置，并计算当前音频段的 RMS"""
        if self.pcmData is None or self.lastOffset >= self.numFrames:
            return False

        currentTime = time.time() - self.startTime
        currentOffset = int(currentTime * self.sampleRate)

        if currentOffset == self.lastOffset:
            return True

        currentOffset = min(currentOffset, self.numFrames)
        dataFragment = self.pcmData[:, self.lastOffset : currentOffset].astype(
            np.float32
        )
        self.currentRms = np.sqrt(np.mean(np.square(dataFragment)))
        self.lastOffset = currentOffset
        return True
