# 定义函数描述
functions = [
    {
        "name": "internet_search",
        "description": "使用关键字在DuckDuckgo上进行内容搜索",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "查询关键词"},
                "region": {
                    "type": "string",
                    "description": "搜索区域, 例如，'zh-cn'代表中文, 'us-en'代表英语, 或'jp-ja'代表日语, 默认'zh-cn'",
                },
                "search_type": {
                    "type": "string",
                    "description": "搜索类型('text' or 'news'), 默认test",
                },
                "max_results": {"type": "integer", "description": "最大返回结果数, 默认10个结果"},
            },
            "required": ["query"],
        },
    }
]


# 定义函数实现
def internet_search(
    query: str, region: str = "zh-cn", search_type: str = "text", max_results: int = 10
) -> list[str]:
    """
    使用关键字在DuckDuckgo上进行内容搜索

    Args:
        query (str): 查询关键词.
        region (str): 搜索区域，例如，'zh-cn'代表中文，'us-en'代表英语，或'jp-ja'代表日语.
        search_type (str): 搜索类型 ('text' or 'news').
        max_results (int): 最大返回结果数.

    Returns:
        list: A list of dictionaries containing search results.
    """
    from duckduckgo_search import DDGS

    if not query.strip():
        raise ValueError("Query cannot be empty!")

    # Ensure the query is a valid UTF-8 string
    query = query.encode("utf-8").decode("utf-8")

    if not query.strip():
        raise ValueError("Query cannot be empty!")

    results = []
    try:
        with DDGS() as ddgs:
            if search_type == "text":
                results = [
                    r for r in ddgs.text(query, region=region, max_results=max_results)
                ]
            elif search_type == "news":
                results = [
                    r for r in ddgs.news(query, region=region, max_results=max_results)
                ]
            else:
                raise ValueError("Invalid search type! Use 'text' or 'news'.")
    except Exception as e:
        print(f"Error during search: {e}")

    return results


if __name__ == "__main__":
    query = input("Enter your search query: ")
    region = "zh-cn"
    search_type = "text"
    max_results = 10

    try:
        results = internet_search(query, region, search_type, max_results)
        for idx, result in enumerate(results):
            print(f"Result {idx + 1}: {result}")
    except Exception as e:
        print(f"An error occurred: {e}")
