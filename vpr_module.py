# vpr_module.py (声纹识别)

import numpy as np
import os, uuid, pickle
from modelscope.pipelines import pipeline
import logging
from logging_config import gcww

# 获取根记录器
logger = logging.getLogger("vpr_module")


class VoicePrintRecognition:
    def __init__(self, main_settings):
        self.settings = main_settings
        self.database_dir = gcww(self.settings, "database_dir", "./database", logger)
        os.makedirs(self.database_dir, exist_ok=True)  # 确保数据库目录存在
        self.sample_db_path = os.path.join(self.database_dir, "voicePrintDB.pkl")
        self.vpr_model = gcww(
            self.settings,
            "vpr_model",
            "damo/speech_campplus_sv_zh-cn_16k-common",
            logger,
        )
        self.similarity_threshold = gcww(
            self.settings, "vpr_similarity_threshold", 0.7, logger
        )
        self.vpr_match_only = gcww(self.settings, "vpr_match_only", None, logger)

        # 初始化声纹识别模型
        self.sv_pipeline = pipeline(
            task="speaker-verification",
            model=self.vpr_model,
            model_revision="v1.0.0",
        )

        # 初始化样本数据库，加载现有数据
        self.voicePrintDB = self._load_sample_db()

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
            pickle.dump(self.voicePrintDB, f)

    def register_voiceprint(self, audio_frames, person_name=None):
        """注册新的声纹样本

        Args:
            audio_frames (bytes): 音频序列
            person_name (str, optional): 注册用户名称. Defaults to None.

        Returns:
            int: 声纹UID
        """
        if len(audio_frames) == 0:
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
        self.voicePrintDB[unique_id] = sample_info
        self._save_sample_db()  # 将数据库同步保存到磁盘

        logger.info(f"{person_name}声纹注册成功")

        return unique_id

    def remove_voiceprint(self, unique_id=None, person_name=None):
        """删除声纹库指定数据

        Args:
            unique_id (int, optional): 声纹UID. Defaults to None.
            person_name (str, optional): 用户名. Defaults to None.

        Returns:
            bool: 是否成功删除
        """
        _return_flag = False

        if unique_id == None and person_name == None:
            logger.warning("请输入声纹的unique_id或person_name")
            return False

        if unique_id:  # 匹配unique_id
            for _id, _ in list(self.voicePrintDB.items()):
                if _id == unique_id:
                    _return_flag = True
                    del self.voicePrintDB[_id]
                    logger.info(f"{unique_id}声纹删除成功")

        if person_name:  # 匹配person_name
            for _id, sample_info in list(self.voicePrintDB.items()):
                _person_name = sample_info["person_name"]
                if _person_name == person_name:
                    _return_flag = True
                    del self.voicePrintDB[_id]
                    logger.info(f"{person_name}声纹删除成功")

        self._save_sample_db()  # 将数据库同步保存到磁盘

        return _return_flag

    def list_voiceprint(self):
        """查看声纹库数据"""
        for _id, sample_info in self.voicePrintDB.items():
            _person_name = sample_info["person_name"]
            logger.info(f"voicePrintDB: {_person_name}_{_id}")

    def match_voiceprint(self, audio_frames):
        """比对输入的音频序列声纹是否与样本库中任何数据匹配

        Args:
            audio_frames (bytes): 音频序列

        Returns:
            str: 匹配到的用户名称, 失配则返回"Unknown"
        """
        if len(audio_frames) == 0:
            logger.debug("match_voiceprint: audio_frames为空")
            return "Unknown"
        audio_data = np.concatenate(audio_frames, axis=0)
        result = self.sv_pipeline([audio_data], output_emb=True)
        input_embedding = result["embs"][0]
        best_match_percent = 0
        best_match_person = "Unknown"  # 如果无匹配对象超过分数阈值, 返回Unknown

        # 遍历样本库比对
        for _, sample_info in self.voicePrintDB.items():
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
                # 结果维护匹配分数最高的声纹对象
                if best_match_percent < similarity_percentage:
                    best_match_percent = similarity_percentage
                    best_match_person = sample_info["person_name"]
        return best_match_person

    def compare_two_voiceprints(self, audio_frames1, audio_frames2):
        """比对两个音频声纹序列是否匹配

        Args:
            audio_frames1 (bytes): 音频序列1
            audio_frames2 (bytes): 音频序列2

        Returns:
            bool: 是否匹配
        """
        if len(audio_frames1) == 0 or len(audio_frames2) == 0:
            logger.warning("compare_two_voiceprints: 输入音频序列为空")
            return False
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
    import pyaudio, logging_config, yaml

    # 初始化日志配置
    logging_config.setup_logging()

    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    # 初始化声纹管理器
    voice_manager = VoicePrintRecognition(settings)

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

    voice_manager.list_voiceprint()

    # logger.debug(voice_manager.remove_voiceprint(person_name="ayo"))

    # voice_manager.list_voiceprint()

    # 注册新的声纹样本
    person_name = "Tor"  # 改成你自己的名称, 记得要和prompt对齐, 这样模型才能识别是你
    voice_id = voice_manager.register_voiceprint(temp_frames, person_name)
    print(f"注册成功，声纹ID: {voice_id}")

    # 比对输入音频序列是否与库中的样本匹配
    # is_match = voice_manager.match_voiceprint(temp_frames)
    # print(f"输入音频与样本库匹配: {is_match}")

    # 比对两个音频序列是否匹配
    # is_match_two = voice_manager.compare_two_voiceprints(
    #     temp_frames, temp_frames
    # )  # 举例使用相同的音频
    # print(f"两个音频匹配: {is_match_two}")
