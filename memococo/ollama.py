import requests
from memococo.config import logger

def query_ollama(question, base_url="http://127.0.0.1:11434", model="qwen2.5:3b"):
    url = base_url + "/api/generate"
    #如果未运行ollama服务，则返回question，判断url是否可达，不可达则返回question
    try:
        response = requests.get(base_url)
        if response.status_code != 200:
            logger.warning(f"ollama服务不可达，返回问题：{question}")
            return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"ollama服务不可达，返回问题：{question}")
        return None
    # 定义问题前缀，用于指示模型需要提取关键词
    question_prefix="帮我提取下面这段查询语句的关键词，不要包含聊天、记录、对话、内容这种无意义的关键词，并以json数组的形式返回关键词列表,请注意仅回复json数组内容。查询语句如下:"
    # 将问题前缀与实际问题拼接成完整的问题
    full_question = question_prefix + question

    # 请求头
    headers = { "Content-Type": "application/json" }

    # 请求体
    data = {"model": model,"prompt": full_question, "stream": False }

    try:
        # 发送POST请求
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        return response_json["response"]

    except requests.exceptions.RequestException as e:
        logger.warning(f"请求大模型时出错: {e}")
        return None



if __name__ == "__main__":
    # 发送一个问题给大模型
    question = "帮我整理下面这段查询语句的关键词,并以json数组的形式返回关键词列表,请注意仅回复json数组内容。查询语句如下:查询昨天在汉堡店吃汉堡的聊天记录"
    answer = query_ollama(question)
    logger.info(f"大模型的回复：{answer}")