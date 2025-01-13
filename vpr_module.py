# vpr_module.py (声纹识别)

import numpy as np
import os, uuid, pickle
from modelscope.pipelines import pipeline
import logging

# 获取根记录器
logger = logging.getLogger("vpr_module")


class VoicePrintManager:
    def __init__(
        self,
        sample_dir="voice_samples",
        model="damo/speech_campplus_sv_zh-cn_16k-common",
        similarity_threshold=0.7,  # 默认相似度阈值
    ):
        # 初始化声纹识别模型
        self.sv_pipeline = pipeline(
            task="speaker-verification",
            model=model,
            model_revision="v1.0.0",
        )
        self.sample_dir = sample_dir  # 声纹样本库存储路径
        os.makedirs(self.sample_dir, exist_ok=True)  # 确保样本库目录存在
        self.sample_db_path = os.path.join(self.sample_dir, "sample_db.pkl")

        # 初始化样本数据库，加载现有数据
        self.sample_db = self._load_sample_db()
        self.similarity_threshold = similarity_threshold  # 相似度阈值配置

    def _generate_unique_id(self):
        """生成唯一的ID"""
        return str(uuid.uuid4())

    def _load_sample_db(self):
        """加载持久化的样本数据库"""
        if os.path.exists(self.sample_db_path):
            with open(self.sample_db_path, "rb") as f:
                return pickle.load(f)
        return {}  # 如果没有数据，返回空字典

    def _save_sample_db(self):
        """将样本数据库持久化存储"""
        with open(self.sample_db_path, "wb") as f:
            pickle.dump(self.sample_db, f)

    def register_voiceprint(self, audio_frames, person_name=None):
        """注册新的声纹样本"""
        if not audio_frames:
            logger.warning("输入声纹序列为空")
            return None

        # 生成唯一的ID
        unique_id = self._generate_unique_id()

        # 提取音频的声纹特征（embedding）
        audio_data = np.concatenate(audio_frames, axis=0)  # 合并音频数据
        result = self.sv_pipeline([audio_data], output_emb=True)
        embedding = result["embs"][0]  # 提取声纹特征

        # 保存声纹特征和相关信息
        sample_info = {
            "id": unique_id,
            "embedding": embedding,
            "person_name": person_name,
        }

        # 添加到样本数据库
        self.sample_db[unique_id] = sample_info
        self._save_sample_db()  # 将数据库同步保存到磁盘

        return unique_id

    def match_voiceprint(self, audio_frames):
        """比对输入的音频序列声纹是否与样本库中任何数据匹配"""
        audio_data = np.concatenate(audio_frames, axis=0)
        result = self.sv_pipeline([audio_data], output_emb=True)
        input_embedding = result["embs"][0]
        beat_match_percent = 0
        beat_match_person = None

        # 遍历样本库比对
        for _, sample_info in self.sample_db.items():
            sample_embedding = sample_info["embedding"]
            norm1 = np.linalg.norm(input_embedding)
            norm2 = np.linalg.norm(sample_embedding)
            # 计算标准的余弦相似度
            similarity = np.dot(input_embedding, sample_embedding) / (norm1 * norm2)
            # 转换为范围[0, 1]
            similarity_percentage = (similarity + 1) / 2.0

            logger.debug(
                f"和{sample_info['person_name']}匹配度: {similarity_percentage * 100:.2f}%"
            )
            if similarity_percentage > self.similarity_threshold:  # 使用配置的阈值
                logger.debug(f"匹配声纹: {sample_info['person_name']}")
                # return True
        return False

    def compare_two_voiceprints(self, audio_frames1, audio_frames2):
        """比对两个音频序列是否匹配"""
        audio_data1 = np.concatenate(audio_frames1, axis=0)
        audio_data2 = np.concatenate(audio_frames2, axis=0)

        result1 = self.sv_pipeline([audio_data1], output_emb=True)
        result2 = self.sv_pipeline([audio_data2], output_emb=True)

        embedding1 = result1["embs"][0]
        embedding2 = result2["embs"][0]
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        # 计算标准的余弦相似度
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)

        logger.debug(f"两条音频序列声纹匹配度: {similarity * 100:.2f}%")
        return similarity > self.similarity_threshold  # 使用配置的阈值


# 示例用法
if __name__ == "__main__":
    import pyaudio, logging_config

    # 初始化日志配置
    logging_config.setup_logging()

    # 初始化声纹管理器
    voice_manager = VoicePrintManager()

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024,
    )
    temp_frames = []  # 用来存储音频数据的列表
    try:
        logger.debug("录音线程启动")
        while True:
            data = stream.read(1024, exception_on_overflow=False)
            temp_frames.append(np.frombuffer(data, dtype=np.int16))
    except KeyboardInterrupt:
        logger.debug("录音中断，正在关闭...")
    finally:
        # 停止并关闭音频流
        stream.stop_stream()
        stream.close()
        audio.terminate()
        logger.debug("音频流已关闭")

    # 注册新的声纹样本
    # person_name = "lrq"
    # voice_id = voice_manager.register_voiceprint(temp_frames, person_name)
    # print(f"注册成功，声纹ID: {voice_id}")

    # 比对输入音频序列是否与库中的样本匹配
    is_match = voice_manager.match_voiceprint(temp_frames)
    print(f"输入音频与样本库匹配: {is_match}")

    # 比对两个音频序列是否匹配
    # is_match_two = voice_manager.compare_two_voiceprints(
    #     temp_frames, temp_frames
    # )  # 举例使用相同的音频
    # print(f"两个音频匹配: {is_match_two}")
