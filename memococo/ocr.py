from memococo.config import logger
import cv2
import numpy as np
from typing import List
import time


def extract_text_from_image(image: np.ndarray) -> str:
    """从图像中提取文本

    使用 RapidOCR 进行文本识别

    Args:
        image: 要处理的图像（NumPy数组）

    Returns:
        提取的文本，如果提取失败则返回空字符串
    """
    # 检查图像是否有效
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        logger.error("Invalid image provided for OCR")
        return ""

    # 直接调用 RapidOCR 引擎
    start_time = time.time()

    try:
        result = rapid_ocr(image)

        elapsed_time = time.time() - start_time
        logger.info(f"OCR processing completed in {elapsed_time:.2f} seconds using RapidOCR")

        # 处理结果
        if result is None:
            return ""

        text = ""
        try:
            # rapidocr 返回的是列表
            for item in result:
                text += item[1]
        except Exception as e:
            logger.error(f"Error parsing OCR result: {e}")
            return ""

        return text

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error occurred during OCR processing after {elapsed_time:.2f} seconds: {e}")
        return ""


def rapid_ocr(image: np.ndarray) -> List:
    """使用RapidOCR进行图像文本提取

    优化版本：增强图像预处理、优化参数配置

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

            # 图像增强，提高识别率
            # 对于截图，通常保留原始图像效果更好
            # 如果识别率低，可以尝试取消下面的注释
            # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 转为灰度图
            # image = cv2.GaussianBlur(image, (3, 3), 0)  # 高斯模糊减少噪点

        # 导入 RapidOCR
        from rapidocr_onnxruntime import RapidOCR

        # 使用RapidOCR进行图像文本提取，使用优化参数
        engine = RapidOCR(params={
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
        })

        # 执行OCR识别
        result, _ = engine(image)  # 忽略引擎返回的耗时

        return result
    except ImportError as e:
        logger.error(f"RapidOCR not installed or not found: {e}")
        logger.error("Please install RapidOCR: pip install rapidocr-onnxruntime")
        return []
    except Exception as e:
        logger.error(f"Error in rapid_ocr: {e}")
        return []


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
