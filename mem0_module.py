# mem0_module.py

from mem0 import Memory
from datetime import datetime
import logging
from logging_config import gcww

# 获取根记录器
logger = logging.getLogger("modle_module")


class Mem0Client:
    def __init__(self):
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "mem0",
                    "host": "localhost",
                    "port": 6333,
                    "embedding_model_dims": 768,  # Change this according to your embedder's dimensions
                },
            },
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": "qwen2.5:7b",
                    "temperature": 0,
                    "max_tokens": 131072,
                    "ollama_base_url": "http://localhost:11434",  # Ensure this URL is correct
                },
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": "nomic-embed-text:latest",
                    # Alternatively, you can use "snowflake-arctic-embed:latest"
                    "ollama_base_url": "http://localhost:11434",
                },
            },
        }

        self.memory_client = Memory.from_config(config)

    def add_mem(self, user_text: str, bot_text: str, user_id: str = "Unknown"):
        messages = [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": bot_text},
        ]
        self.memory_client.add(messages, user_id=user_id)

    def search_mem(self, query: str, user_id: str = "Unknown"):
        results = self.memory_client.search(query, user_id)
        return results

    def get_all_mem(self, user_id: str):
        user_memories = self.memory_client.get_all(user_id=user_id)
        return user_memories

    def del_all_mem(self, user_id: str):
        self.memory_client.delete_all(user_id=user_id)


class memModule(Mem0Client):
    def __init__(self):
        super().__init__()
        self.client = Mem0Client()
        self.pre_user_name = "Unknown"
        self.pre_user_content = ""

    def _convert_iso_to_chinese(self, iso_str):
        """解析ISO格式的时间字符串"""
        weekdays_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        dt = datetime.fromisoformat(iso_str)
        weekday = weekdays_cn[dt.weekday()]
        return dt.strftime("%Y年%m月%d日 %H时%M分%S秒 ") + weekday

    def _format_memory_entry(self, data: dict) -> str:
        """将记忆数据结构转换为自然语言格式

        Args:
            data: 包含记忆数据的字典，应包含以下字段：
                - memory: 记忆内容（必需）
                - score: 置信度分数（可选）
                - created_at: 创建时间（可选）
                - updated_at: 更新时间（可选）
                - user_id: 用户ID（可选）

        Returns:
            str: 自然语言格式的文本描述
        """
        memory = data.get("memory", "")
        if not memory:
            return ""
        details = []
        # 处理置信度分数
        if "score" in data:
            details.append(f"记忆相关度: {round(data['score'] * 100, 1)}%")
        # 处理时间信息
        time_info = []
        for field, label in [
            ("created_at", "创建时间"),
            ("updated_at", "更新时间"),
        ]:
            if timestamp := data.get(field):
                try:
                    time_cn = self._convert_iso_to_chinese(timestamp)
                    time_info.append(f"{label}: {time_cn}")
                except (ValueError, TypeError):
                    pass
        details.extend(time_info)
        # 处理用户ID
        user_id = data.get("user_id")
        return f"\t与{user_id}有关的记忆: {memory} " + (
            f"({', '.join(details)})" if details else ""
        )

    def recall_mem(self, user_name: str, input_text: str):
        """召回与用户话题相关记忆

        Args:
            user_name (str): 用户名称
            input_text (str): 用户输入

        Returns:
            str: 与用户话题相关的记忆信息
        """
        if input_text == "":
            logger.warning("记忆召回异常, input_text为空!")
            return ""
        self.pre_user_name, self.pre_user_content = user_name, input_text
        mem_list = self.search_mem(input_text, user_name)
        mem_prompt = "以下是可能与用户和话题相关的记忆:"
        mem_entrys = ""
        for mem_dict in mem_list:
            mem_entrys += "\n" + self._format_memory_entry(mem_dict)
        result = mem_prompt + mem_entrys + "\n\n"
        logger.debug(f"召回记忆: {result}")
        return result

    def record_mem(self, bot_rsp_text: str):
        """记录用户话题相关记忆

        Args:
            bot_rsp_text (str): 模型返回内容
        """
        if self.pre_user_content == "":
            logger.warning("记忆记录异常, pre_input为空!")
            return
        # 这里采用记录最近一次调用recall的信息作为用户数据的输入
        self.add_mem(self.pre_user_content, bot_rsp_text, self.pre_user_name)
        logger.debug(f"成功记录记忆")


# 使用示例
if __name__ == "__main__":
    import logging_config, yaml

    # 初始化日志配置
    logging_config.setup_logging()
    """加载配置文件"""
    with open("./config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    client = memModule()

    print(f"\n记忆召回: \n{client.recall_mem('zzr', '有什么水果推荐吗')}\n")

    client.record_mem("我知道你喜欢吃香蕉")
