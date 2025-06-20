import requests
from memococo.config import logger
import json
import time
import re
from typing import List, Optional
import concurrent.futures

def extract_keywords_to_json(keywords: str, model: str = "qwen2.5:3b", base_url: str = "http://127.0.0.1:11434", timeout: int = 10) -> List[str]:
    """从查询语句中提取关键词并返回json格式

    优化版本：增加超时处理、错误重试和结果验证

    Args:
        keywords: 要提取关键词的查询语句
        model: 使用的Ollama模型名称
        base_url: Ollama服务的基础URL
        timeout: 请求超时时间（秒）

    Returns:
        关键词列表，如果提取失败则返回空列表
    """
    # 如果关键词为空，直接返回空列表
    if not keywords or not keywords.strip():
        return []

    # 构建提示语句
    question_prefix = """帮我提取下面这段查询语句的关键词，不要包含聊天、记录、对话、内容这种无意义的关键词。
请仅返回一个JSON格式的关键词数组，不要有任何其他文字。例如：["keyword1", "keyword2"]
查询语句如下："""
    full_question = question_prefix + keywords.strip()

    # 使用线程池并设置超时
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(query_ollama, full_question, model, base_url)
        try:
            answer = future.result(timeout=timeout)
            if not answer:
                logger.warning("Failed to extract keywords: No response from Ollama")
                return []

            #移除可能的<think></think>标签与里面的内容
            answer = re.sub(r'<think>.*?</think>', '', answer)

            # 尝试直接解析JSON
            try:
                # 先尝试直接解析整个响应
                result = json.loads(answer)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取JSON部分
                try:
                    # 尝试提取方括号中的内容
                    if '[' in answer and ']' in answer:
                        json_str = answer[answer.find('['):answer.rfind(']')+1]
                        result = json.loads(json_str)
                        if isinstance(result, list):
                            return result
                except json.JSONDecodeError:
                    pass

            # 如果上述方法都失败，尝试更宽松的提取
            try:
                # 尝试提取所有可能的JSON数组
                json_arrays = re.findall(r'\[.*?\]', answer)
                for json_array in json_arrays:
                    try:
                        result = json.loads(json_array)
                        if isinstance(result, list):
                            return result
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                logger.error(f"Error extracting JSON arrays: {e}")

            # 如果所有方法都失败，回退到简单分词
            logger.warning(f"Failed to parse JSON from Ollama response, falling back to simple tokenization")
            # 移除特殊字符并按空格分词
            words = keywords.strip().replace(',', ' ').replace('.', ' ').split()
            return [word for word in words if len(word) > 1]  # 只返回长度大于1的词

        except concurrent.futures.TimeoutError:
            logger.error(f"Keyword extraction timed out after {timeout} seconds")
            return []
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []

def query_ollama(question: str, model: str = "qwen2.5:3b", base_url: str = "http://127.0.0.1:11434", max_retries: int = 2, timeout: int = 30) -> Optional[str]:
    """向Ollama发送查询请求

    优化版本：增加重试机制、超时控制和错误处理

    Args:
        question: 要发送给模型的问题
        model: 使用的Ollama模型名称
        base_url: Ollama服务的基础URL
        max_retries: 最大重试次数
        timeout: 请求超时时间（秒）

    Returns:
        模型的响应文本，如果请求失败则返回None
    """
    url = base_url + "/api/generate"

    # 检查Ollama服务是否可用
    try:
        response = requests.get(base_url, timeout=5)  # 设置较短的超时时间检查服务可用性
        if response.status_code != 200:
            logger.warning(f"Ollama服务返回非200状态码: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Ollama服务不可达: {e}")
        return None

    # 请求头和请求体
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": question,
        "stream": False,
        # 可以添加其他参数来控制生成，如temperature、max_tokens等
        "temperature": 0.1,  # 使用较低的温度以获得更确定的结果
    }

    # 实现重试机制
    retries = 0
    last_error = None

    while retries <= max_retries:
        try:
            start_time = time.time()
            logger.info(f"Sending request to Ollama (attempt {retries+1}/{max_retries+1})")

            # 发送POST请求并设置超时
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
            response.raise_for_status()

            # 解析响应
            response_json = response.json()
            elapsed_time = time.time() - start_time
            logger.info(f"Ollama response received in {elapsed_time:.2f} seconds")

            return response_json.get("response")

        except requests.exceptions.Timeout:
            logger.warning(f"Request to Ollama timed out after {timeout} seconds (attempt {retries+1}/{max_retries+1})")
            last_error = "Timeout"
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error when querying Ollama: {e} (attempt {retries+1}/{max_retries+1})")
            last_error = str(e)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error querying Ollama: {e} (attempt {retries+1}/{max_retries+1})")
            last_error = str(e)
        except Exception as e:
            logger.warning(f"Unexpected error when querying Ollama: {e} (attempt {retries+1}/{max_retries+1})")
            last_error = str(e)

        # 增加重试计数并等待一段时间再重试
        retries += 1
        if retries <= max_retries:
            wait_time = 2 ** retries  # 指数退避策略
            logger.info(f"Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)

    logger.error(f"Failed to query Ollama after {max_retries+1} attempts. Last error: {last_error}")
    return None



if __name__ == "__main__":
    # 发送一个问题给大模型
    qwen = "qwen2.5:3b"
    gemma = "gemma3:4b"
    question = "返回一个json数组，从0-10"
    # answer = query_ollama(question, model = gemma)
    # logger.info(f"大模型的回复：{answer}")
    answer = extract_keywords_to_json(question,model = qwen)
    logger.info(f"大模型的回复：{answer}")