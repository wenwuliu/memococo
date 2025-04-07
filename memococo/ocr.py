import requests
import base64
from memococo.config import logger
import json
import cv2
import numpy as np
from typing import List, Dict, Optional, Union
import concurrent.futures
import time


def extract_text_from_image(image: np.ndarray, ocr_engine: str = 'trwebocr', timeout: int = 15) -> str:
    """从图像中提取文本

    优化版本：增加超时处理、并行处理和错误恢复

    Args:
        image: 要处理的图像（NumPy数组）
        ocr_engine: 要使用的OCR引擎，默认为'trwebocr'
        timeout: 处理超时时间（秒）

    Returns:
        提取的文本，如果提取失败则返回空字符串
    """
    # 检查图像是否有效
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        logger.error("Invalid image provided for OCR")
        return ""

    # 使用线程池并设置超时
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 根据选择的OCR引擎提交任务
        if ocr_engine == 'tesseract':
            future = executor.submit(tesseract_ocr, image)
        elif ocr_engine == 'trwebocr':
            future = executor.submit(trwebocr, image)
        elif ocr_engine == 'rapidocr':
            future = executor.submit(rapid_ocr, image)
        else:
            logger.error(f'Invalid OCR engine: {ocr_engine}')
            return ""

        try:
            # 等待结果，并设置超时
            start_time = time.time()
            result = future.result(timeout=timeout)
            elapsed_time = time.time() - start_time
            logger.info(f"OCR processing completed in {elapsed_time:.2f} seconds using {ocr_engine}")

            # 处理结果
            if result is None:
                return ""

            text = ""
            try:
                if ocr_engine == 'tesseract':
                    # Tesseract返回的是JSON字符串
                    for item in json.loads(result):
                        text += item[1]
                elif ocr_engine == 'trwebocr':
                    # trwebocr返回的是JSON字符串
                    for item in json.loads(result):
                        text += item[1]
                elif ocr_engine == 'rapidocr':
                    # rapidocr返回的是列表
                    for item in result:
                        text += item[1]
            except Exception as e:
                logger.error(f"Error parsing OCR result: {e}")
                return ""

            return text

        except concurrent.futures.TimeoutError:
            logger.error(f"OCR processing timed out after {timeout} seconds")
            return ""
        except Exception as e:
            logger.error(f"Error occurred during OCR processing: {e}")
            return ""

def rapid_ocr(image: np.ndarray) -> List:
    """使用RapidOCR进行图像文本提取

    优化版本：增加错误处理、性能监控和日志记录

    Args:
        image: 要处理的图像（NumPy数组）

    Returns:
        识别结果列表
    """
    try:
        # 图像预处理，提高OCR识别率
        if image is not None and image.size > 0:
            # 如果图像太大，进行缩放以提高性能
            h, w = image.shape[:2]
            if max(h, w) > 2000:
                scale = 2000 / max(h, w)
                new_h, new_w = int(h * scale), int(w * scale)
                image = cv2.resize(image, (new_w, new_h))
                logger.info(f"Resized image from {h}x{w} to {new_h}x{new_w} for OCR processing")

            # 可选的图像增强
            # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 转为灰度图
            # image = cv2.GaussianBlur(image, (3, 3), 0)  # 高斯模糊减少噪点

        from rapidocr_onnxruntime import RapidOCR
        start_time = time.time()

        # 使用RapidOCR进行图像文本提取
        engine = RapidOCR(params={
            "Global.lang_det": "ch_server",
            "Global.lang_rec": "ch_server",
            # 可以添加其他参数来提高识别率
        })

        result, elapse_time = engine(image)
        elapsed_time = time.time() - start_time

        # 记录性能指标
        recognized_count = len(result) if result else 0
        logger.info(f"RapidOCR processed image in {elapsed_time:.2f}s, found {recognized_count} text regions")

        return result
    except ImportError as e:
        logger.error(f"RapidOCR not installed or not found: {e}")
        return []
    except Exception as e:
        logger.error(f"Error in rapid_ocr: {e}")
        return []

def tesseract_ocr(image: np.ndarray) -> str:
    """使用Tesseract OCR进行图像文本提取

    优化版本：增加错误处理、性能监控和日志记录

    Args:
        image: 要处理的图像（NumPy数组）

    Returns:
        JSON格式的识别结果字符串
    """
    try:
        import pytesseract
        from pytesseract import Output

        start_time = time.time()

        # 图像预处理，提高OCR识别率
        try:
            binary_image = image_preprocessing(image)
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original image: {e}")
            binary_image = image

        # 设置Tesseract配置
        config = '--oem 3 --psm 6'  # 使用LSTM OCR引擎，假设单个文本块

        # 识别文本
        out = pytesseract.image_to_data(binary_image, output_type=Output.DICT, lang='chi_sim+eng', config=config)

        # 处理结果
        result = []
        num_boxes = len(out['level'])
        text_count = 0

        for i in range(num_boxes):
            # 只包含非空文本
            if out['text'][i].strip():
                (x, y, w, h) = (out['left'][i], out['top'][i], out['width'][i], out['height'][i])
                conf = float(out['conf'][i]) if out['conf'][i] != '-1' else 0
                text = out['text'][i]
                result.append([[x, y, w, h, conf], text, 1])
                text_count += 1

        # 记录性能指标
        elapsed_time = time.time() - start_time
        logger.info(f"Tesseract OCR processed image in {elapsed_time:.2f}s, found {text_count} text regions")

        # 将result转为json字符串，中文编码为unicode
        result_json = json.dumps(result, ensure_ascii=False)
        return result_json

    except ImportError as e:
        logger.error(f"Tesseract not installed or not found: {e}")
        return json.dumps([])
    except Exception as e:
        logger.error(f"Error in tesseract_ocr: {e}")
        return json.dumps([])

def trwebocr(image: np.ndarray) -> Optional[str]:
    """使用trwebocr进行图像文本提取

    优化版本：增加错误处理、超时控制和重试机制

    Args:
        image: 要处理的图像（NumPy数组）

    Returns:
        JSON格式的识别结果字符串，如果失败则返回None
    """
    url = "http://127.0.0.1:8089/api/tr-run/"
    max_retries = 0  # 最大重试次数
    timeout = 10  # 超时时间（秒）

    # 图像预处理
    try:
        start_time = time.time()

        # 图像压缩，减小传输大小
        h, w = image.shape[:2]
        if max(h, w) > 1500:
            scale = 1500 / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            image = cv2.resize(image, (new_w, new_h))
            logger.info(f"Resized image from {h}x{w} to {new_h}x{new_w} for trwebocr")

        # 将图像转换为PNG格式的字节流
        _, buffer = cv2.imencode('.png', image)
        encoded_string = base64.b64encode(buffer).decode('utf-8')

        # 实现重试机制
        retries = 0
        while retries <= max_retries:
            try:
                logger.info(f"Sending request to trwebocr (attempt {retries+1}/{max_retries+1})")

                # 发送POST请求并设置超时
                result = requests.post(
                    url,
                    data={"img": encoded_string, 'compress': 0},
                    timeout=timeout
                )
                result.raise_for_status()

                # 解析响应
                data = result.json()
                elapsed_time = time.time() - start_time

                if "data" in data and "raw_out" in data["data"]:
                    text = data["data"]["raw_out"]
                    text_count = len(text) if isinstance(text, list) else 0
                    logger.info(f"trwebocr processed image in {elapsed_time:.2f}s, found {text_count} text regions")

                    # 将text转为json字符串，中文编码为unicode
                    return json.dumps(text, ensure_ascii=False)
                else:
                    logger.warning(f"Unexpected response format from trwebocr: {data}")
                    return None

            except requests.exceptions.Timeout:
                logger.warning(f"Request to trwebocr timed out after {timeout}s (attempt {retries+1}/{max_retries+1})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error connecting to trwebocr: {e} (attempt {retries+1}/{max_retries+1})")
            except Exception as e:
                logger.warning(f"Unexpected error with trwebocr: {e} (attempt {retries+1}/{max_retries+1})")

            # 增加重试计数并等待一段时间再重试
            retries += 1
            if retries <= max_retries:
                wait_time = 2 ** retries  # 指数退避策略
                logger.info(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)

        logger.error(f"Failed to connect to trwebocr after {max_retries+1} attempts")
        return None

    except Exception as e:
        logger.error(f"Error preparing image for trwebocr: {e}")
        return None

def image_preprocessing(image):
    # 图像灰度化
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray_image

def easy_ocr(image):
    image = image_preprocessing(image)
    import easyocr
    reader = easyocr.Reader(['ch_sim','en'],gpu=True)
    result = reader.readtext(image,detail=0)
    # 将result字符串数组转为字符串，按空格分隔
    result = " ".join(result)
    return result

# main方法测试
if __name__ == "__main__":
    import time
    start_time = time.time()
    screenshots = []
    import mss
    import numpy as np
    with mss.mss() as sct:
        for monitor in range(len(sct.monitors)):
            logger.info(f"截取第{monitor}个屏幕")
            monitor_ = sct.monitors[monitor]
            screenshot = np.array(sct.grab(monitor_))
            screenshot = screenshot[:, :, [2, 1, 0]]
            screenshots.append(screenshot)
        response = extract_text_from_image(screenshots[0],ocr_engine='rapid_ocr')
        end_time = time.time()
        logger.info("seperate")
        logger.info(response)
        logger.info(f"耗时：{end_time - start_time}")
        #将json数组中所有的第二个元素抽取出来，并拼接成字符串
