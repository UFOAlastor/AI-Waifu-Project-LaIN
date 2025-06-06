# replyParser_module.py

import re
import logging

# 获取根记录器
logger = logging.getLogger("replyParser_module")


def replyParser(reply: str, delimiter: str = "|||"):
    """解析 {表情}|||{中文}|||{日语} 格式的字符串，确保对分隔符冲突的处理安全。

    Args:
        reply (str): 模型回复文本
        delimiter (str, optional): 文本分割符. Defaults to "|||".

    Returns:
        json: 解析后数据
    """

    # 1. 检查 reply 是否为字符串类型
    if not isinstance(reply, str):
        if isinstance(reply, dict):
            logger.debug(f"reply is a dict: {reply}")
            if "error" in reply:
                logger.error(f"reply has error: {reply}")
                return {"status": 400, "message": f"解析内容报错: {reply.get('error')}"}
        return {"status": 400, "message": f"解析内容异常: {reply}"}

    # 2. 去掉首尾空格、换行符等无效字符
    reply = reply.strip()

    # 3. 检查是否为空字符串
    if not reply:
        return {"status": 400, "message": "解析内容为空"}

    # 4. 替换掉可能冲突的分隔符（如多余的空格）
    reply = re.sub(r"\s+", " ", reply)

    # 5. 转义分隔符
    escaped_delimiter = re.escape(delimiter)

    # 6. 正则匹配的模式，确保两边有空格、换行符都被正确忽略
    pattern = rf"^(.*?)\s*{escaped_delimiter}\s*(.*?)\s*{escaped_delimiter}\s*(.*?)$"

    # 7. 使用 try-except 捕获正则匹配错误
    try:
        match = re.match(pattern, reply)
    except Exception as e:
        return {"status": 500, "message": f"正则表达式匹配失败，错误: {e}"}

    # 8. 检查匹配结果
    if not match:
        return {
            "status": 400,
            "message": "解析内容格式不正确，应为 {表情}|||{中文}|||{日语}",
        }

    # 9. 提取结果
    expression, chinese, japanese = match.groups()

    # 10. 清理多余空格
    return {
        "status": 0,
        "message": "解析成功",
        "data": {
            "ep": expression.strip(),
            "zh": chinese.strip(),
            "jp": japanese.strip(),
        },
    }


if __name__ == "__main__":
    import logging_config

    # 初始化日志配置
    logging_config.setup_logging()
    # 测试用例
    test_reply = ""

    logger.debug(f"测试内容: {test_reply}")

    parsed_reply = replyParser(test_reply)
    parse_status = parsed_reply.get("status")
    parse_message = parsed_reply.get("message")

    if not parse_status:
        tachie_expression = parsed_reply.get("data").get("ep")
        Chinese_message = parsed_reply.get("data").get("zh")
        Japanese_message = parsed_reply.get("data").get("jp")
        logger.debug(f"tachie_expression: {tachie_expression}")
        logger.debug(f"Chinese_message: {Chinese_message}")
        logger.debug(f"Japanese_message: {Japanese_message}")
    else:
        logger.debug(f"最终结果: {parse_message}")
