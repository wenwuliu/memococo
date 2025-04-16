"""
OCR引擎工厂模块

根据硬件环境自动选择最合适的OCR引擎：
- 如果有GPU，使用EasyOCR (GPU模式)
- 如果只有CPU，使用RapidOCR (CPU模式)
"""

from memococo.config import logger
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import time
import gc

# OCR引擎类型
OCR_ENGINE_RAPIDOCR = "rapidocr"  # RapidOCR引擎
OCR_ENGINE_EASYOCR = "easyocr"    # EasyOCR引擎
OCR_ENGINE_UMIOCR = "umiocr"      # UmiOCR API引擎

# 导入UmiOCR客户端
try:
    from memococo.umiocr_client import UmiOcrClient
    _umiocr_imported = True
except ImportError:
    _umiocr_imported = False

# 全局OCR引擎，避免重复创建
_ocr_engine = None
_ocr_engine_type = None
_gpu_available = False
_umiocr_client = None
_umiocr_available = None  # None表示未检查，True/False表示检查结果

def check_umiocr_availability() -> bool:
    """检查UmiOCR是否可用

    Returns:
        bool: UmiOCR是否可用
    """
    global _umiocr_client, _umiocr_available, _umiocr_imported

    # 如果已经检查过，直接返回结果
    if _umiocr_available is not None:
        return _umiocr_available

    # 如果没有导入UmiOCR客户端，返回false
    if not _umiocr_imported:
        logger.info("未导入UmiOCR客户端，无法使用UmiOCR")
        _umiocr_available = False
        return False

    try:
        # 创建UmiOCR客户端并检查可用性
        _umiocr_client = UmiOcrClient()
        _umiocr_available = _umiocr_client.is_available()

        if _umiocr_available:
            logger.info("UmiOCR可用，将使用UmiOCR进行OCR识别")
        else:
            logger.info("UmiOCR不可用，将使用其他OCR引擎")

        return _umiocr_available
    except Exception as e:
        logger.error(f"检查UmiOCR可用性时出错: {e}")
        _umiocr_available = False
        return False

def check_gpu_availability() -> bool:
    """检查GPU是否可用

    Returns:
        bool: GPU是否可用
    """
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"检测到GPU: {gpu_name}")
            return True
        else:
            logger.info("未检测到GPU，将使用CPU模式")
            return False
    except ImportError:
        logger.info("未安装PyTorch，无法检测GPU，将使用CPU模式")
        return False
    except Exception as e:
        logger.error(f"检测GPU时出错: {e}")
        return False

def preprocess_image_for_ocr(image: np.ndarray) -> Optional[np.ndarray]:
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

def get_ocr_engine(force_type: Optional[str] = None) -> Tuple[Any, str]:
    """获取OCR引擎实例

    选择OCR引擎的优先级：
    1. 如果强制指定了引擎类型，使用指定的引擎
    2. 如果UmiOCR可用，使用UmiOCR API，因为它速度最快
    3. 如果有GPU，使用EasyOCR (GPU模式)，因为它识别的文本量更多
    4. 如果只有CPU，使用RapidOCR (CPU模式)，因为它在CPU模式下速度更快且准确率更高

    Args:
        force_type: 强制使用指定类型的引擎，可选值: "rapidocr", "easyocr", "umiocr"

    Returns:
        Tuple[Any, str]: (OCR引擎实例, 引擎类型)
    """
    global _ocr_engine, _ocr_engine_type, _gpu_available, _umiocr_client, _umiocr_available

    # 如果引擎已初始化且类型匹配，直接返回
    if _ocr_engine is not None and (force_type is None or force_type == _ocr_engine_type):
        return _ocr_engine, _ocr_engine_type

    # 如果强制指定了引擎类型
    if force_type is not None:
        engine_type = force_type
    else:
        # 1. 首先尝试使用UmiOCR
        if _umiocr_available is None:  # 只在第一次检查
            check_umiocr_availability()

        if _umiocr_available:
            # 如果UmiOCR可用，使用UmiOCR
            engine_type = OCR_ENGINE_UMIOCR
            logger.info("UmiOCR可用，使用UmiOCR进行OCR识别")
        else:
            # 2. 如果UmiOCR不可用，检查GPU可用性
            if _gpu_available is None:  # 只在第一次检查
                _gpu_available = check_gpu_availability()

            # 根据硬件环境选择引擎
            if _gpu_available:
                # 如果有GPU，使用EasyOCR (GPU)
                # 根据测试结果，EasyOCR在GPU模式下识别的文本量更多
                engine_type = OCR_ENGINE_EASYOCR
                logger.info("检测到GPU，使用EasyOCR (GPU模式)")
            else:
                # 如果只有CPU，使用RapidOCR (CPU)
                # 根据测试结果，RapidOCR在CPU模式下速度更快且准确率更高
                engine_type = OCR_ENGINE_RAPIDOCR
                logger.info("未检测到GPU，使用RapidOCR (CPU模式)")

    # 创建引擎实例
    if engine_type == OCR_ENGINE_RAPIDOCR:
        _ocr_engine = create_rapidocr_engine()
        _ocr_engine_type = OCR_ENGINE_RAPIDOCR
    elif engine_type == OCR_ENGINE_EASYOCR:
        _ocr_engine = create_easyocr_engine(use_gpu=_gpu_available)
        _ocr_engine_type = OCR_ENGINE_EASYOCR
    elif engine_type == OCR_ENGINE_UMIOCR:
        # UmiOCR引擎已经在check_umiocr_availability()中创建
        _ocr_engine = _umiocr_client
        _ocr_engine_type = OCR_ENGINE_UMIOCR
    else:
        logger.error(f"不支持的OCR引擎类型: {engine_type}")
        return None, ""

    return _ocr_engine, _ocr_engine_type

def create_rapidocr_engine() -> Any:
    """创建RapidOCR引擎实例

    Returns:
        RapidOCR引擎实例
    """
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

        logger.info("初始化 RapidOCR 引擎 (CPU模式)")

        # 创建RapidOCR实例
        engine = RapidOCR(params=params)
        logger.debug("RapidOCR引擎初始化成功")
        return engine
    except ImportError as e:
        logger.error(f"RapidOCR未安装或未找到: {e}")
        logger.error("请安装RapidOCR: pip install rapidocr-onnxruntime")
        return None
    except Exception as e:
        logger.error(f"初始化RapidOCR引擎失败: {e}")
        return None

def create_easyocr_engine(use_gpu: bool = True) -> Any:
    """创建EasyOCR引擎实例

    Args:
        use_gpu: 是否使用GPU

    Returns:
        EasyOCR引擎实例
    """
    try:
        # 导入 EasyOCR
        import easyocr

        # 检查GPU可用性
        if use_gpu:
            try:
                import torch
                if not torch.cuda.is_available():
                    logger.warning("PyTorch未检测到CUDA，EasyOCR将使用CPU模式")
                    use_gpu = False
                else:
                    logger.info(f"PyTorch检测到CUDA: {torch.cuda.get_device_name(0)}")
            except ImportError:
                logger.warning("未安装PyTorch，EasyOCR将使用CPU模式")
                use_gpu = False

        # 创建EasyOCR实例
        logger.info(f"初始化 EasyOCR 引擎 ({'GPU' if use_gpu else 'CPU'}模式)")

        # 支持中文和英文
        engine = easyocr.Reader(['ch_sim', 'en'], gpu=use_gpu)
        logger.debug("EasyOCR引擎初始化成功")
        return engine
    except ImportError as e:
        logger.error(f"EasyOCR未安装或未找到: {e}")
        logger.error("请安装EasyOCR: pip install easyocr")
        return None
    except Exception as e:
        logger.error(f"初始化EasyOCR引擎失败: {e}")
        return None

def perform_ocr(engine: Any, engine_type: str, image: np.ndarray) -> List:
    """使用指定的OCR引擎执行文本识别

    Args:
        engine: OCR引擎实例
        engine_type: 引擎类型
        image: 要处理的图像

    Returns:
        识别结果列表
    """
    if engine is None:
        return []

    try:
        if engine_type == OCR_ENGINE_RAPIDOCR:
            # RapidOCR处理
            result, _ = engine(image)  # 忽略引擎返回的耗时
            return result
        elif engine_type == OCR_ENGINE_EASYOCR:
            # EasyOCR处理
            result = engine.readtext(image)
            return result
        elif engine_type == OCR_ENGINE_UMIOCR:
            # UmiOCR处理
            result = engine.recognize(image)
            return result
        else:
            logger.error(f"不支持的OCR引擎类型: {engine_type}")
            return []
    except Exception as e:
        logger.error(f"OCR处理错误 ({engine_type}): {e}")
        return []

def extract_text_from_ocr_result(result: List, engine_type: str) -> str:
    """从OCR结果中提取文本

    Args:
        result: OCR识别结果
        engine_type: 引擎类型

    Returns:
        提取的文本
    """
    if not result:
        return ""

    text = ""
    try:
        if engine_type == OCR_ENGINE_RAPIDOCR:
            # RapidOCR结果格式: [[box, text, score], ...]
            for item in result:
                text += item[1]
        elif engine_type == OCR_ENGINE_EASYOCR:
            # EasyOCR结果格式: [[box, text, score], ...]
            for item in result:
                if len(item) >= 2:
                    text += item[1] + " "
            text = text.strip()
        elif engine_type == OCR_ENGINE_UMIOCR:
            # UmiOCR结果格式: [{"text": "...", "score": 0.9, ...}, ...]
            for item in result:
                text += item.get("text", "") + " "
            text = text.strip()
        else:
            logger.error(f"不支持的OCR引擎类型: {engine_type}")
    except Exception as e:
        logger.error(f"提取文本时出错 ({engine_type}): {e}")

    return text

def extract_text_from_image(image: np.ndarray) -> str:
    """从图像中提取文本

    根据硬件环境自动选择最合适的OCR引擎

    Args:
        image: 要处理的图像（NumPy数组）

    Returns:
        提取的文本，如果提取失败则返回空字符串
    """
    # 检查图像是否有效
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        logger.error("无效的图像")
        return ""

    start_time = time.time()

    try:
        # 图像预处理
        processed_image = preprocess_image_for_ocr(image)
        if processed_image is None:
            return ""

        # 获取OCR引擎
        engine, engine_type = get_ocr_engine()
        if engine is None:
            return ""

        # 执行OCR识别
        result = perform_ocr(engine, engine_type, processed_image)

        # 提取文本
        text = extract_text_from_ocr_result(result, engine_type)

        elapsed_time = time.time() - start_time
        logger.debug(f"OCR处理完成，使用 {engine_type}，耗时 {elapsed_time:.2f} 秒")

        return text

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"OCR处理出错，耗时 {elapsed_time:.2f} 秒: {e}")
        return ""

def extract_text_from_images_batch(images: List[np.ndarray]) -> List[str]:
    """批量从多个图像中提取文本

    根据硬件环境自动选择最合适的OCR引擎

    Args:
        images: 要处理的图像列表（NumPy数组列表）

    Returns:
        提取的文本列表，如果某个图像提取失败则对应位置为空字符串
    """
    if not images:
        return []

    # 过滤无效图像
    valid_images = []
    valid_indices = []
    for i, image in enumerate(images):
        if image is not None and isinstance(image, np.ndarray) and image.size > 0:
            processed = preprocess_image_for_ocr(image)
            if processed is not None:
                valid_images.append(processed)
                valid_indices.append(i)

    if not valid_images:
        return ["" for _ in range(len(images))]

    # 批量处理图像
    start_time = time.time()
    results = ["" for _ in range(len(images))]

    try:
        # 获取OCR引擎
        engine, engine_type = get_ocr_engine()
        if engine is None:
            return results

        # 逐个处理图像
        for i, img in enumerate(valid_images):
            result = perform_ocr(engine, engine_type, img)
            text = extract_text_from_ocr_result(result, engine_type)

            # 将结果放回原始位置
            results[valid_indices[i]] = text

        elapsed_time = time.time() - start_time
        logger.info(f"批量OCR处理完成，使用 {engine_type}，耗时 {elapsed_time:.2f} 秒，处理了 {len(valid_images)} 张图像")

        return results

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"批量OCR处理出错，耗时 {elapsed_time:.2f} 秒: {e}")
        return results

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
        logger.info(f"总耗时：{end_time - start_time:.2f}秒")
