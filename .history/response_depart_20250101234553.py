import re

def parse_reply(reply: str, delimiter: str = "|||"):
    """
    解析 {表情}|||{中文}|||{日语} 格式的字符串，确保对分隔符冲突的处理安全。
    :param reply: 输入的字符串，格式如 {表情}|||{中文}|||{日语}
    :param delimiter: 自定义分隔符，默认为 "|||"
    :return: 一个包含 表情, 中文, 日语 的字典
    """
    # 将分隔符进行正则转义，确保匹配时安全
    escaped_delimiter = re.escape(delimiter)

    # 使用正则表达式确保划分三部分
    pattern = rf"^(.*?)\s*{escaped_delimiter}\s*(.*?)\s*{escaped_delimiter}\s*(.*?)$"
    match = re.match(pattern, reply)

    if not match:
        raise ValueError(
            f"输入字符串格式不正确，应为 {{表情}}{delimiter}{{中文}}{delimiter}{{日语}}"
        )

    # 提取三部分内容
    expression, chinese, japanese = match.groups()

    return {
        "表情": expression.strip(),
        "中文": chinese.strip(),
        "日语": japanese.strip(),
    }

# 测试用例
test_reply = "高兴|||这是包含|符号的中文|||これは|記号を含む日本語です"
print("测试内容:", test_reply)
result = parse_reply(test_reply)
print("解析结果:", result)

