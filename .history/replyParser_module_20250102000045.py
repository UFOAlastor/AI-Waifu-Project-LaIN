import re


def parse_reply(reply: str, delimiter: str = "|||"):
    """
    解析 {表情}|||{中文}|||{日语} 格式的字符串，确保对分隔符冲突的处理安全。
    :param reply: 输入的字符串，格式如 {表情}|||{中文}|||{日语}
    :param delimiter: 自定义分隔符，默认为 "|||"
    :return: 一个包含 表情, 中文, 日语 的字典
    """
    # 1. 检查 reply 是否为字符串类型
    if not isinstance(reply, str):
        raise TypeError(f"输入值必须是字符串类型，但接收到的是 {type(reply)}")

    # 2. 去掉首尾空格、换行符等无效字符
    reply = reply.strip()

    # 3. 检查是否为空字符串
    if not reply:
        raise ValueError("输入字符串为空，无法解析。")

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
        raise ValueError(f"正则表达式匹配失败，输入: {reply}, 错误: {e}")

    # 8. 检查匹配结果
    if not match:
        raise ValueError(
            f"输入字符串格式不正确，应为 {{表情}}{delimiter}{{中文}}{delimiter}{{日语}}"
        )

    # 9. 提取结果
    expression, chinese, japanese = match.groups()

    # 10. 清理多余空格
    return {
        "表情": expression.strip(),
        "中文": chinese.strip(),
        "日语": japanese.strip(),
    }


if __name__ == "__main__":
    # 测试用例
    # test_reply = "思考 ||| 现在是晚上11点57分，距离明天凌晨12点还有3分钟。||| 現在は午後11時57分です。明日の午前0時まであと3分です。"
    # test_reply = "思考 ||| 现在是晚上11点57分，\n距离明天凌晨12点还有3分钟。||| 現在は午後11時57分です。明日の午前0時まであと3分です。"
    test_reply = ""

    print("测试内容:", test_reply)
    result = parse_reply(test_reply)
    print("解析结果-表情:", result.get("表情"))
    print("解析结果-中文:", result.get("中文"))
    print("解析结果-日语:", result.get("日语"))
