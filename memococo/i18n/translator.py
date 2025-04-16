"""
翻译器模块

提供文本翻译功能
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from flask import request, session

# 默认语言
DEFAULT_LOCALE = 'zh_CN'

# 当前语言
_current_locale = DEFAULT_LOCALE

# 翻译数据缓存
_translations: Dict[str, Dict[str, str]] = {}

# 日志记录器
logger = logging.getLogger('memococo.i18n')

class Translator:
    """翻译器类"""
    
    def __init__(self, locale: str = None):
        """初始化翻译器
        
        Args:
            locale: 语言代码，如zh_CN、en_US等
        """
        self.locale = locale or _current_locale
        self._ensure_translations_loaded(self.locale)
    
    def translate(self, key: str, default: str = None, **kwargs) -> str:
        """翻译文本
        
        Args:
            key: 文本键名
            default: 默认文本，当找不到翻译时返回
            **kwargs: 格式化参数
            
        Returns:
            str: 翻译后的文本
        """
        # 如果找不到翻译，使用默认文本或键名
        if self.locale not in _translations or key not in _translations[self.locale]:
            result = default or key
        else:
            result = _translations[self.locale][key]
        
        # 格式化文本
        if kwargs:
            try:
                result = result.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format key in translation: {e}")
            except Exception as e:
                logger.error(f"Error formatting translation: {e}")
        
        return result
    
    def __call__(self, key: str, default: str = None, **kwargs) -> str:
        """翻译文本（简写形式）
        
        Args:
            key: 文本键名
            default: 默认文本，当找不到翻译时返回
            **kwargs: 格式化参数
            
        Returns:
            str: 翻译后的文本
        """
        return self.translate(key, default, **kwargs)

def _load_translations(locale: str) -> Dict[str, str]:
    """加载翻译数据
    
    Args:
        locale: 语言代码
        
    Returns:
        Dict[str, str]: 翻译数据
    """
    # 获取翻译文件路径
    file_path = os.path.join(os.path.dirname(__file__), 'locales', f'{locale}.json')
    
    # 如果文件不存在，返回空字典
    if not os.path.exists(file_path):
        logger.warning(f"Translation file not found: {file_path}")
        return {}
    
    # 加载翻译数据
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading translation file: {e}")
        return {}

def _ensure_translations_loaded(locale: str) -> None:
    """确保翻译数据已加载
    
    Args:
        locale: 语言代码
    """
    if locale not in _translations:
        _translations[locale] = _load_translations(locale)

def get_translator(locale: str = None) -> Translator:
    """获取翻译器
    
    Args:
        locale: 语言代码，如果为None则使用当前语言
        
    Returns:
        Translator: 翻译器实例
    """
    return Translator(locale)

def set_locale(locale: str) -> None:
    """设置当前语言
    
    Args:
        locale: 语言代码
    """
    global _current_locale
    
    # 确保语言代码有效
    if locale not in get_available_locales():
        logger.warning(f"Invalid locale: {locale}, fallback to {DEFAULT_LOCALE}")
        locale = DEFAULT_LOCALE
    
    _current_locale = locale
    
    # 预加载翻译数据
    _ensure_translations_loaded(locale)

def get_locale() -> str:
    """获取当前语言
    
    Returns:
        str: 当前语言代码
    """
    # 优先使用会话中的语言设置
    if hasattr(session, 'locale'):
        return session.locale
    
    # 其次使用请求中的语言设置
    if hasattr(request, 'accept_languages'):
        # 获取浏览器支持的语言列表
        locales = get_available_locales()
        for locale in request.accept_languages.values():
            if locale[:2] in [l[:2] for l in locales]:
                return locale
    
    # 最后使用默认语言
    return _current_locale

def get_available_locales() -> List[str]:
    """获取可用的语言列表
    
    Returns:
        List[str]: 可用的语言代码列表
    """
    # 获取locales目录下的所有JSON文件
    locales_dir = os.path.join(os.path.dirname(__file__), 'locales')
    if not os.path.exists(locales_dir):
        return [DEFAULT_LOCALE]
    
    # 获取所有JSON文件名（不含扩展名）
    locales = []
    for file_name in os.listdir(locales_dir):
        if file_name.endswith('.json'):
            locales.append(file_name[:-5])
    
    return locales if locales else [DEFAULT_LOCALE]
