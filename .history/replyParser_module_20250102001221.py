import re


def replyParser(reply: str, delimiter: str = "|||"):
    """
    解析 {表情}|||{中文}|||{日语} 格式的字符串，确保对分隔符冲突的处理安全。
    :param reply: 输入的字符串，格式如 {表情}|||{中文}|||{日语}
    :param delimiter: 自定义分隔符，默认为 "|||"
    :return: 包含 status code 和 message 的字典，包含成功或错误的提示
    """
    # 1. 检查 reply 是否为字符串类型
    if not isinstance(reply, str):
        return {"status": 400, "message": "输入值必须是字符串类型"}

    # 2. 去掉首尾空格、换行符等无效字符
    reply = reply.strip()

    # 3. 检查是否为空字符串
    if not reply:
        return {"status": 400, "message": "输入字符串为空，无法解析。"}

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
            "message": "输入字符串格式不正确，应为 {表情}|||{中文}|||{日语}",
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
    # 测试用例
    # test_reply = "思考 ||| 现在是晚上11点57分，距离明天凌晨12点还有3分钟。||| 現在は午後11時57分です。明日の午前0時まであと3分です。"
    # test_reply = "思考 ||| 现在是晚上11点57分，\n距离明天凌晨12点还有3分钟。||| 現在は午後11時57分です。明日の午前0時まであと3分です。"
    # test_reply = ""
    test_reply = "思考 ||| 这是一个无效的输入||| 12345"

    print("测试内容:", test_reply)

    parsed_reply = replyParser(test_reply)
    parse_status = parsed_reply.get("status")
    parse_message = parsed_reply.get("message")

    Chinese_message = parse_message

    if not parse_status:
        tachie_expression = parsed_reply.get("data").get("ep")
        Chinese_message = parsed_reply.get("data").get("zh")
        Japanese_message = parsed_reply.get("data").get("jp")
        print("tachie_expression:", tachie_expression)
        print("Chinese_message:", Chinese_message)
        print("Japanese_message:", Japanese_message)

    print("最终结果:", Chinese_message)
