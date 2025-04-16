"""
格式化器模块

提供日期、时间和数字的本地化格式化功能
"""

import datetime
import locale
import logging
from typing import Optional, Union, Dict, Any
from babel.dates import format_date as babel_format_date
from babel.dates import format_time as babel_format_time
from babel.dates import format_datetime as babel_format_datetime
from babel.numbers import format_number as babel_format_number

from memococo.i18n.translator import get_locale

# 日志记录器
logger = logging.getLogger('memococo.i18n')

# 日期格式映射
DATE_FORMATS = {
    'short': 'short',
    'medium': 'medium',
    'long': 'long',
    'full': 'full',
}

# 时间格式映射
TIME_FORMATS = {
    'short': 'short',
    'medium': 'medium',
    'long': 'long',
    'full': 'full',
}

# 语言区域映射
LOCALE_MAPPING = {
    'zh_CN': 'zh_Hans_CN',
    'en_US': 'en_US',
    'ja_JP': 'ja_JP',
    'ko_KR': 'ko_KR',
    'fr_FR': 'fr_FR',
    'de_DE': 'de_DE',
    'es_ES': 'es_ES',
    'it_IT': 'it_IT',
    'ru_RU': 'ru_RU',
}

def _get_babel_locale(locale_code: str) -> str:
    """获取Babel支持的语言区域代码
    
    Args:
        locale_code: 语言区域代码
        
    Returns:
        str: Babel支持的语言区域代码
    """
    return LOCALE_MAPPING.get(locale_code, locale_code)

def format_date(
    date: Union[datetime.date, datetime.datetime, int, float],
    format: str = 'medium',
    locale_code: str = None
) -> str:
    """格式化日期
    
    Args:
        date: 日期对象、datetime对象或时间戳
        format: 格式化类型，可选值：short, medium, long, full
        locale_code: 语言区域代码，如果为None则使用当前语言
        
    Returns:
        str: 格式化后的日期字符串
    """
    # 转换日期对象
    if isinstance(date, (int, float)):
        date = datetime.datetime.fromtimestamp(date).date()
    elif isinstance(date, datetime.datetime):
        date = date.date()
    
    # 获取语言区域
    locale_code = locale_code or get_locale()
    babel_locale = _get_babel_locale(locale_code)
    
    # 获取格式化类型
    format_type = DATE_FORMATS.get(format, 'medium')
    
    try:
        return babel_format_date(date, format=format_type, locale=babel_locale)
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        # 回退到默认格式
        return date.strftime('%Y-%m-%d')

def format_time(
    time: Union[datetime.time, datetime.datetime, int, float],
    format: str = 'medium',
    locale_code: str = None
) -> str:
    """格式化时间
    
    Args:
        time: 时间对象、datetime对象或时间戳
        format: 格式化类型，可选值：short, medium, long, full
        locale_code: 语言区域代码，如果为None则使用当前语言
        
    Returns:
        str: 格式化后的时间字符串
    """
    # 转换时间对象
    if isinstance(time, (int, float)):
        time = datetime.datetime.fromtimestamp(time).time()
    elif isinstance(time, datetime.datetime):
        time = time.time()
    
    # 获取语言区域
    locale_code = locale_code or get_locale()
    babel_locale = _get_babel_locale(locale_code)
    
    # 获取格式化类型
    format_type = TIME_FORMATS.get(format, 'medium')
    
    try:
        return babel_format_time(time, format=format_type, locale=babel_locale)
    except Exception as e:
        logger.error(f"Error formatting time: {e}")
        # 回退到默认格式
        return time.strftime('%H:%M:%S')

def format_datetime(
    dt: Union[datetime.datetime, int, float],
    format: str = 'medium',
    locale_code: str = None
) -> str:
    """格式化日期时间
    
    Args:
        dt: datetime对象或时间戳
        format: 格式化类型，可选值：short, medium, long, full
        locale_code: 语言区域代码，如果为None则使用当前语言
        
    Returns:
        str: 格式化后的日期时间字符串
    """
    # 转换datetime对象
    if isinstance(dt, (int, float)):
        dt = datetime.datetime.fromtimestamp(dt)
    
    # 获取语言区域
    locale_code = locale_code or get_locale()
    babel_locale = _get_babel_locale(locale_code)
    
    # 获取格式化类型
    format_type = DATE_FORMATS.get(format, 'medium')
    
    try:
        return babel_format_datetime(dt, format=format_type, locale=babel_locale)
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        # 回退到默认格式
        return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_number(
    number: Union[int, float],
    decimal_places: int = None,
    locale_code: str = None
) -> str:
    """格式化数字
    
    Args:
        number: 数字
        decimal_places: 小数位数
        locale_code: 语言区域代码，如果为None则使用当前语言
        
    Returns:
        str: 格式化后的数字字符串
    """
    # 获取语言区域
    locale_code = locale_code or get_locale()
    babel_locale = _get_babel_locale(locale_code)
    
    try:
        # 如果指定了小数位数，先进行四舍五入
        if decimal_places is not None:
            number = round(number, decimal_places)
        
        return babel_format_number(number, locale=babel_locale)
    except Exception as e:
        logger.error(f"Error formatting number: {e}")
        # 回退到默认格式
        return str(number)
