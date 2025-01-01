import re

import re


def parse_reply(reply: str, delimiter: str = "|||"):
    """
    解析 {表情}|||{中文}|||{日语} 格式的字符串，确保对分隔符冲突的处理安全。
    :param reply: 输入的字符串，格式如 {表情}|||{中文}|||{日语}
    :param delimiter: 自定义分隔符，默认为 "|||"
    :return: 一个包含 表情, 中文, 日语 的字典
    """
    # 检查类型
    if not isinstance(reply, str):
        raise TypeError(f"输入值必须是字符串类型，但接收到的是 {type(reply)}")

    # 检查是否为空字符串
    if not reply.strip():
        raise ValueError("输入字符串为空，无法解析。")

    # 转义分隔符
    escaped_delimiter = re.escape(delimiter)

    # 正则匹配
    pattern = rf"^(.*?)\s*{escaped_delimiter}\s*(.*?)\s*{escaped_delimiter}\s*(.*?)$"
    try:
        match = re.match(pattern, reply)
    except Exception as e:
        raise ValueError(f"正则表达式匹配失败，输入: {reply}, 错误: {e}")

    if not match:
        raise ValueError(
            f"输入字符串格式不正确，应为 {{表情}}{delimiter}{{中文}}{delimiter}{{日语}}"
        )

    # 提取内容
    expression, chinese, japanese = match.groups()

    return {
        "表情": expression.strip(),
        "中文": chinese.strip(),
        "日语": japanese.strip(),
    }


if __name__ == "__main__":
    # 测试用例
    test_reply = "高兴|||这是包含|符号的中文|||これは|記号を含む日本語です"
    print("测试内容:", test_reply)
    result = parse_reply(test_reply)
    print("解析结果-表情:", result.get("表情"))
    print("解析结果-中文:", result.get("中文"))
    print("解析结果-日语:", result.get("日语"))
