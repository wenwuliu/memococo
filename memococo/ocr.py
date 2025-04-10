from memococo.config import logger
import cv2
import numpy as np
from typing import List
import time

def extract_text_from_image(image: np.ndarray) -> str:
    """从图像中提取文本

    使用RapidOCR进行文本识别

    Args:
        image: 要处理的图像（NumPy数组）

    Returns:
        提取的文本，如果提取失败则返回空字符串
    """
    # 检查图像是否有效
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        logger.error("Invalid image provided for OCR")
        return ""

    # 使用RapidOCR
    start_time = time.time()

    try:
        result = rapid_ocr(image)

        elapsed_time = time.time() - start_time
        logger.debug(f"RapidOCR processing completed in {elapsed_time:.2f} seconds")

        # 处理结果
        if result is None:
            return ""

        text = ""
        try:
            # rapidocr 返回的是列表
            for item in result:
                text += item[1]
        except Exception as e:
            logger.error(f"Error parsing RapidOCR result: {e}")
            return ""

        return text

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error occurred during RapidOCR processing after {elapsed_time:.2f} seconds: {e}")
        return ""


def extract_text_from_images_batch(images: List[np.ndarray]) -> List[str]:
    """批量从多个图像中提取文本

    使用RapidOCR进行批量文本识别

    Args:
        images: 要处理的图像列表（NumPy数组列表）

    Returns:
        提取的文本列表，如果某个图像提取失败则对应位置为空字符串
    """
    if not images:
        return []

    # 使用RapidOCR
    # 过滤无效图像
    valid_images = []
    valid_indices = []
    for i, image in enumerate(images):
        if image is not None and isinstance(image, np.ndarray) and image.size > 0:
            valid_images.append(image)
            valid_indices.append(i)

    if not valid_images:
        return ["" for _ in range(len(images))]

    # 直接调用 RapidOCR 引擎进行批量处理
    start_time = time.time()
    results = ["" for _ in range(len(images))]

    try:
        # 批量处理图像
        batch_results = rapid_ocr_batch(valid_images)

        elapsed_time = time.time() - start_time
        logger.info(f"Batch RapidOCR processing completed in {elapsed_time:.2f} seconds for {len(valid_images)} images")

        # 处理结果
        for i, result in enumerate(batch_results):
            if result is None:
                continue

            text = ""
            try:
                # rapidocr 返回的是列表
                for item in result:
                    text += item[1]

                # 将结果放回原始位置
                results[valid_indices[i]] = text
            except Exception as e:
                logger.error(f"Error parsing RapidOCR result for image {i}: {e}")

        return results

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error occurred during batch RapidOCR processing after {elapsed_time:.2f} seconds: {e}")
        return results


# 全局OCR引擎，避免重复创建
_ocr_engine = None

def get_ocr_engine():
    """获取全局OCR引擎实例

    Returns:
        RapidOCR引擎实例
    """
    global _ocr_engine

    # 如果引擎已初始化，直接返回
    if _ocr_engine is not None:
        return _ocr_engine

    try:
        # 导入 RapidOCR
        from rapidocr_onnxruntime import RapidOCR

        # 基本参数
        params = {
            "Global.lang_det": "ch_server",
            "Global.lang_rec": "ch_server",
            "Global.use_angle_cls": True,  # 启用角度检测，处理旋转文本
            "Global.use_text_det": True,   # 启用文本检测
            "Global.use_text_rec": True,   # 启用文本识别
            "Det.limit_side_len": 960,     # 限制输入图像的最大边长，提高速度
            "Det.limit_type": "min",       # 缩放类型，保持长宽比
            "Det.thresh": 0.3,             # 检测置信度阈值，降低可提高速度但可能降低准确率
            "Rec.rec_batch_num": 6,        # 识别批处理数量，提高并行处理能力
            "Rec.rec_img_h": 32,           # 识别图像高度
            "Rec.rec_img_w": 320,          # 识别图像宽度
            "Cls.cls_batch_num": 6,        # 角度分类批处理数量
            "Cls.cls_thresh": 0.9,         # 角度分类置信度阈值
        }

        logger.info("Using CPU for OCR processing")

        # 创建RapidOCR实例
        _ocr_engine = RapidOCR(params=params)
        logger.debug("RapidOCR engine initialized successfully")
    except ImportError as e:
        logger.error(f"RapidOCR not installed or not found: {e}")
        logger.error("Please install RapidOCR: pip install rapidocr-onnxruntime")
        return None
    except Exception as e:
        logger.error(f"Error initializing RapidOCR engine: {e}")
        return None

    return _ocr_engine

def preprocess_image_for_ocr(image: np.ndarray) -> np.ndarray:
    """预处理图像用于OCR识别

    Args:
        image: 原始图像

    Returns:
        预处理后的图像
    """
    if image is None or image.size == 0:
        return None

    # 如果图像太大，进行缩放以提高性能
    h, w = image.shape[:2]
    if max(h, w) > 2000:
        scale = 2000 / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        image = cv2.resize(image, (new_w, new_h))

    return image

def rapid_ocr(image: np.ndarray) -> List:
    """使用RapidOCR进行图像文本提取

    优化版本：使用全局引擎实例，避免重复创建

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
        engine = get_ocr_engine()
        if engine is None:
            return []

        # 执行OCR识别
        result, _ = engine(image)  # 忽略引擎返回的耗时

        return result
    except Exception as e:
        logger.error(f"Error in rapid_ocr: {e}")
        return []

def rapid_ocr_batch(images: List[np.ndarray]) -> List[List]:
    """批量使用RapidOCR进行图像文本提取

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
        engine = get_ocr_engine()
        if engine is None:
            return [[] for _ in range(len(images))]

        # 逐个处理图像，但使用同一个引擎实例
        # 注意：RapidOCR目前不支持真正的批处理API，但使用同一个引擎实例可以减少初始化开销
        results = []
        for img in processed_images:
            result, _ = engine(img)  # 忽略引擎返回的耗时
            results.append(result)

        return results
    except Exception as e:
        logger.error(f"Error in rapid_ocr_batch: {e}")
        return [[] for _ in range(len(images))]


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

        logger.info("OCR 结果:")
        logger.info(response)
        logger.info(f"耗时：{end_time - start_time:.2f}秒")
