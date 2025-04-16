"""
UmiOCR API客户端

提供与UmiOCR API通信的功能，用于OCR文本识别。
"""

import requests
import base64
import cv2
import numpy as np
import time
from typing import List, Dict, Any, Optional, Tuple
from memococo.config import logger

# UmiOCR API配置
UMIOCR_API_URLS = [
    "http://127.0.0.1:1224/api/ocr",  # 默认UmiOCR API地址
    "http://localhost:1224/api/ocr",  # 使用localhost
]

class UmiOcrClient:
    """UmiOCR API客户端"""
    
    def __init__(self):
        """初始化UmiOCR API客户端"""
        self.api_url = None
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查UmiOCR API是否可用
        
        Returns:
            bool: API是否可用
        """
        for api_url in UMIOCR_API_URLS:
            try:
                # 尝试ping接口
                ping_url = api_url.replace("/ocr", "/ping")
                logger.debug(f"尝试连接UmiOCR API: {api_url}")
                response = requests.get(ping_url, timeout=2)
                
                if response.status_code == 200:
                    self.api_url = api_url
                    logger.info(f"UmiOCR API可用: {api_url}")
                    return True
            except Exception as e:
                logger.debug(f"尝试连接 {api_url} 时出错: {e}")
        
        # 尝试直接访问主页
        try:
            for base_url in ["http://127.0.0.1:1224", "http://localhost:1224"]:
                logger.debug(f"尝试访问UmiOCR主页: {base_url}")
                response = requests.get(base_url, timeout=2)
                if response.status_code == 200:
                    self.api_url = f"{base_url}/api/ocr"
                    logger.info(f"UmiOCR主页可访问: {base_url}")
                    return True
        except Exception as e:
            logger.debug(f"尝试访问UmiOCR主页时出错: {e}")
        
        logger.info("UmiOCR API不可用")
        return False
    
    def is_available(self) -> bool:
        """检查UmiOCR API是否可用
        
        Returns:
            bool: API是否可用
        """
        return self.available and self.api_url is not None
    
    def recognize(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """识别图像中的文本
        
        Args:
            image: 要处理的图像
        
        Returns:
            识别结果列表，每个结果包含文本、位置和置信度
        """
        if not self.is_available():
            logger.error("UmiOCR API不可用")
            return []
        
        try:
            # 将图像编码为base64
            _, buffer = cv2.imencode('.png', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # 准备请求数据
            data = {
                "base64": img_base64,
                "options": {
                    "cls": True  # 启用文本方向检测
                }
            }
            
            # 发送请求
            start_time = time.time()
            response = requests.post(self.api_url, json=data, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"UmiOCR API请求失败: {response.status_code}")
                return []
            
            # 解析响应
            result = response.json()
            elapsed_time = time.time() - start_time
            
            if "code" not in result or result["code"] != 100:
                logger.error(f"UmiOCR API返回错误: {result}")
                return []
            
            logger.debug(f"UmiOCR处理完成，耗时 {elapsed_time:.2f} 秒")
            return result.get("data", [])
        
        except Exception as e:
            logger.error(f"UmiOCR API处理出错: {e}")
            return []
    
    def extract_text(self, image: np.ndarray) -> str:
        """从图像中提取文本
        
        Args:
            image: 要处理的图像
        
        Returns:
            提取的文本，如果提取失败则返回空字符串
        """
        results = self.recognize(image)
        if not results:
            return ""
        
        text = ""
        for item in results:
            text += item.get("text", "") + " "
        
        return text.strip()
