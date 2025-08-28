"""
Windows 11检测模块

提供检测Windows 11操作系统的功能，并处理兼容性问题
"""

import sys
import platform
import ctypes
from ctypes import windll, byref, c_ubyte, c_ushort, c_ulong, Structure, POINTER
import tkinter as tk
from tkinter import messagebox
import logging

# 创建日志记录器
logger = logging.getLogger("win11_detector")

# Windows 11的最低构建版本号
WIN11_MIN_BUILD = 22000

class OSVERSIONINFOEXW(Structure):
    """Windows操作系统版本信息结构体"""
    _fields_ = [
        ('dwOSVersionInfoSize', c_ulong),
        ('dwMajorVersion', c_ulong),
        ('dwMinorVersion', c_ulong),
        ('dwBuildNumber', c_ulong),
        ('dwPlatformId', c_ulong),
        ('szCSDVersion', c_ushort * 128),
        ('wServicePackMajor', c_ushort),
        ('wServicePackMinor', c_ushort),
        ('wSuiteMask', c_ushort),
        ('wProductType', c_ubyte),
        ('wReserved', c_ubyte)
    ]

def get_windows_version_info():
    """
    获取详细的Windows版本信息
    
    Returns:
        dict: 包含Windows版本信息的字典
    """
    try:
        # 检查是否为Windows系统
        if sys.platform != 'win32':
            return {
                'is_windows': False,
                'major_version': 0,
                'minor_version': 0,
                'build_number': 0,
                'platform': sys.platform
            }
        
        # 使用platform模块获取基本信息
        win_ver = platform.win32_ver()
        
        # 使用Windows API获取更详细的版本信息
        os_version = OSVERSIONINFOEXW()
        os_version.dwOSVersionInfoSize = ctypes.sizeof(OSVERSIONINFOEXW)
        
        # 使用RtlGetVersion代替GetVersionEx（后者可能被Windows修改返回值）
        DWORD = c_ulong
        PVOID = POINTER(c_ulong)
        NTSTATUS = DWORD
        
        # 获取ntdll.dll中的RtlGetVersion函数
        rtlGetVersion = windll.ntdll.RtlGetVersion
        rtlGetVersion.restype = NTSTATUS
        rtlGetVersion.argtypes = [PVOID]
        
        # 调用RtlGetVersion获取真实版本信息
        rtlGetVersion(byref(os_version))
        
        # 构建版本信息字典
        version_info = {
            'is_windows': True,
            'major_version': os_version.dwMajorVersion,
            'minor_version': os_version.dwMinorVersion,
            'build_number': os_version.dwBuildNumber,
            'platform': sys.platform,
            'version_string': win_ver[0],
            'service_pack': win_ver[1],
            'win32_edition': platform.win32_edition() if hasattr(platform, 'win32_edition') else None
        }
        
        logger.debug(f"检测到Windows版本: {version_info}")
        return version_info
    
    except Exception as e:
        logger.error(f"获取Windows版本信息时出错: {e}")
        # 返回基本信息
        return {
            'is_windows': sys.platform == 'win32',
            'major_version': 0,
            'minor_version': 0,
            'build_number': 0,
            'platform': sys.platform,
            'error': str(e)
        }

def is_windows_11():
    """
    检测当前操作系统是否为Windows 11
    
    Windows 11的标识特征是:
    - 主版本号为10
    - 构建版本号大于等于22000
    
    Returns:
        bool: 如果是Windows 11则返回True，否则返回False
    """
    try:
        version_info = get_windows_version_info()
        
        # 检查是否为Windows系统
        if not version_info['is_windows']:
            logger.debug("非Windows操作系统")
            return False
        
        # Windows 11的特征是Windows 10 (主版本号10)，但构建版本号大于等于22000
        is_win11 = (
            version_info['major_version'] == 10 and 
            version_info['build_number'] >= WIN11_MIN_BUILD
        )
        
        logger.info(f"Windows 11检测结果: {'是' if is_win11 else '否'}, 构建版本: {version_info['build_number']}")
        return is_win11
    
    except Exception as e:
        logger.error(f"检测Windows 11时出错: {e}")
        return False

def show_compatibility_error():
    """
    显示操作系统不兼容错误消息
    
    当检测到非Windows 11系统时，显示错误消息并退出应用程序
    """
    try:
        # 创建一个隐藏的根窗口
        root = tk.Tk()
        root.withdraw()
        
        # 显示错误消息
        messagebox.showerror(
            "操作系统不兼容",
            "MemoCoco仅支持Windows 11操作系统。\n\n"
            "检测到您正在使用不兼容的操作系统版本。\n"
            "请在Windows 11上运行此应用程序。"
        )
        
        # 销毁窗口
        root.destroy()
        
        logger.warning("显示了操作系统不兼容错误消息")
        
        # 退出应用程序
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"显示兼容性错误消息时出错: {e}")
        # 如果GUI显示失败，则打印到控制台
        print("错误: MemoCoco仅支持Windows 11操作系统。请在Windows 11上运行此应用程序。")
        sys.exit(1)

def check_windows_11_compatibility():
    """
    检查Windows 11兼容性并在不兼容时显示错误
    
    如果不是Windows 11，则显示错误消息并退出应用程序
    
    Returns:
        bool: 如果是Windows 11则返回True
    """
    if not is_windows_11():
        show_compatibility_error()
        return False
    return True

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 测试Windows版本检测
    version_info = get_windows_version_info()
    print(f"Windows版本信息: {version_info}")
    
    # 测试Windows 11检测
    is_win11 = is_windows_11()
    print(f"是否为Windows 11: {is_win11}")
    
    # 如果不是Windows 11，显示错误消息
    if not is_win11:
        show_compatibility_error()