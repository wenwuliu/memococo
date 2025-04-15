from memococo.config import logger
import cv2
import numpy as np
from typing import List
import time

# 导入OCR工厂模块
from memococo.ocr_factory import (
    extract_text_from_image as factory_extract_text_from_image,
    extract_text_from_images_batch as factory_extract_text_from_images_batch,
    preprocess_image_for_ocr,
    check_gpu_availability,
    get_ocr_engine,
    perform_ocr
)

# 兼容原有接口
def extract_text_from_image(image: np.ndarray) -> str:
    """从图像中提取文本

    根据硬件环境自动选择最合适的OCR引擎

    Args:
        image: 要处理的图像（NumPy数组）

    Returns:
        提取的文本，如果提取失败则返回空字符串
    """
    return factory_extract_text_from_image(image)

def extract_text_from_images_batch(images: List[np.ndarray]) -> List[str]:
    """批量从多个图像中提取文本

    根据硬件环境自动选择最合适的OCR引擎

    Args:
        images: 要处理的图像列表（NumPy数组列表）

    Returns:
        提取的文本列表，如果某个图像提取失败则对应位置为空字符串
    """
    return factory_extract_text_from_images_batch(images)

# 兼容原有接口
def rapid_ocr(image: np.ndarray) -> List:
    """使用OCR引擎进行图像文本提取

    注意：此函数保留为兼容原有代码，实际使用的引擎可能是RapidOCR或EasyOCR

    Args:
        image: 要处理的图像（NumPy数组）

    Returns:
        识别结果列表
    """
    try:
        # 图像预处理
        image = preprocess_image_for_ocr(image)
        if image is None:
            return []

        # 获取OCR引擎
        engine, engine_type = get_ocr_engine()
        if engine is None:
            return []

        # 执行OCR识别
        return perform_ocr(engine, engine_type, image)
    except Exception as e:
        logger.error(f"Error in OCR processing: {e}")
        return []

# 兼容原有接口
def rapid_ocr_batch(images: List[np.ndarray]) -> List[List]:
    """批量使用OCR引擎进行图像文本提取

    注意：此函数保留为兼容原有代码，实际使用的引擎可能是RapidOCR或EasyOCR

    Args:
        images: 图像列表

    Returns:
        识别结果列表的列表
    """
    if not images:
        return []

    try:
        # 预处理图像
        processed_images = []
        for image in images:
            processed = preprocess_image_for_ocr(image)
            if processed is not None:
                processed_images.append(processed)

        if not processed_images:
            return [[] for _ in range(len(images))]

        # 获取OCR引擎
        engine, engine_type = get_ocr_engine()
        if engine is None:
            return [[] for _ in range(len(images))]

        # 逐个处理图像
        results = []
        for img in processed_images:
            result = perform_ocr(engine, engine_type, img)
            results.append(result)

        return results
    except Exception as e:
        logger.error(f"Error in batch OCR processing: {e}")
        return [[] for _ in range(len(images))]

# 保留原有的图像预处理函数
def preprocess_image(image: np.ndarray) -> np.ndarray:
    """图像预处理，提高OCR识别率

    Args:
        image: 原始图像

    Returns:
        处理后的图像
    """
    # 转换为灰度图
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 自适应二值化
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # 降噪
    kernel = np.ones((1, 1), np.uint8)
    processed_image = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    return processed_image


# 测试代码
if __name__ == "__main__":
    import mss

    # 检查GPU可用性
    gpu_available = check_gpu_availability()
    print(f"GPU可用性: {gpu_available}")

    # 获取OCR引擎
    engine, engine_type = get_ocr_engine()
    print(f"使用的OCR引擎: {engine_type}")

    start_time = time.time()
    screenshots = []

    with mss.mss() as sct:
        for monitor in range(len(sct.monitors)):
            logger.info(f"截取第{monitor}个屏幕")
            monitor_ = sct.monitors[monitor]
            screenshot = np.array(sct.grab(monitor_))
            screenshot = screenshot[:, :, [2, 1, 0]]
            screenshots.append(screenshot)

        response = extract_text_from_image(screenshots[0])
        end_time = time.time()

        logger.info(f"OCR 结果 ({engine_type}):")
        logger.info(response)
        logger.info(f"耗时：{end_time - start_time:.2f}秒")
