"""
Windows 11截图模块

提供Windows 11特定的截图功能，包括DPI感知和多显示器支持
"""

import sys
import logging
import numpy as np
from PIL import Image, ImageGrab
import ctypes
from ctypes import windll, byref, c_int, Structure, sizeof

# 导入Windows 11窗口管理模块
from memococo.common.win11_window_manager import Win11WindowManager

# 导入Windows 11权限管理模块
from memococo.common.win11_permission_manager import (
    check_screenshot_permission,
    request_screenshot_permission,
    show_permission_error
)

# 创建日志记录器
logger = logging.getLogger("win11_screenshot")

# 定义DPI感知类型
PROCESS_DPI_UNAWARE = 0
PROCESS_SYSTEM_DPI_AWARE = 1
PROCESS_PER_MONITOR_DPI_AWARE = 2

class Win11ScreenshotManager:
    """Windows 11截图管理类，提供DPI感知的截图功能"""
    
    @staticmethod
    def set_process_dpi_awareness():
        """
        设置进程的DPI感知级别为每显示器DPI感知
        
        Returns:
            bool: 设置是否成功
        """
        try:
            # 尝试使用Windows 8.1及更高版本的API
            try:
                windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
                logger.debug("成功设置进程为每显示器DPI感知")
                return True
            except AttributeError:
                # 如果不支持，回退到Windows Vista/7的API
                windll.user32.SetProcessDPIAware()
                logger.debug("成功设置进程为系统DPI感知")
                return True
        except Exception as e:
            logger.warning(f"设置DPI感知级别时出错: {e}")
            return False
    
    @staticmethod
    def get_dpi_scale_factor(hwnd=None):
        """
        获取指定窗口或主显示器的DPI缩放因子
        
        Args:
            hwnd: 窗口句柄，如果为None则获取主显示器
            
        Returns:
            float: DPI缩放因子
        """
        try:
            # 设置DPI感知
            Win11ScreenshotManager.set_process_dpi_awareness()
            
            # 获取DPI缩放因子
            if hwnd:
                return Win11WindowManager.get_window_dpi_scaling(hwnd)
            else:
                # 获取主显示器的DPI
                dc = windll.user32.GetDC(0)
                dpi_x = windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
                windll.user32.ReleaseDC(0, dc)
                return dpi_x / 96.0  # 96 DPI是标准DPI
        except Exception as e:
            logger.warning(f"获取DPI缩放因子时出错: {e}")
            return 1.0  # 默认缩放因子
    
    @staticmethod
    def capture_screen(monitor_index=0):
        """
        捕获指定显示器的屏幕内容
        
        Args:
            monitor_index: 显示器索引，0表示主显示器
            
        Returns:
            numpy.ndarray: 屏幕截图的numpy数组
        """
        try:
            # 设置DPI感知
            Win11ScreenshotManager.set_process_dpi_awareness()
            
            # 获取显示器信息
            monitors = Win11ScreenshotManager.get_monitor_info()
            if not monitors or monitor_index >= len(monitors):
                logger.warning(f"无效的显示器索引: {monitor_index}")
                # 回退到全屏截图
                screenshot = ImageGrab.grab()
                return np.array(screenshot)
            
            # 获取指定显示器的边界
            monitor = monitors[monitor_index]
            left, top, right, bottom = monitor['bounds']
            
            # 捕获指定区域
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            return np.array(screenshot)
        
        except Exception as e:
            logger.error(f"捕获屏幕时出错: {e}")
            # 尝试使用备用方法
            try:
                screenshot = ImageGrab.grab()
                return np.array(screenshot)
            except Exception as e2:
                logger.error(f"备用截图方法也失败: {e2}")
                return None
    
    @staticmethod
    def capture_all_screens():
        """
        捕获所有显示器的屏幕内容
        
        Returns:
            list: 包含所有显示器截图的numpy数组列表
        """
        try:
            # 检查截图权限
            if not check_screenshot_permission():
                logger.warning("缺少截图权限，尝试请求权限")
                if not request_screenshot_permission():
                    logger.error("用户拒绝授予截图权限")
                    show_permission_error("screenshot")
                    return []
            
            # 设置DPI感知
            Win11ScreenshotManager.set_process_dpi_awareness()
            
            # 获取显示器信息
            monitors = Win11ScreenshotManager.get_monitor_info()
            if not monitors:
                logger.warning("未检测到显示器")
                # 回退到全屏截图
                screenshot = ImageGrab.grab()
                return [np.array(screenshot)]
            
            # 捕获每个显示器
            screenshots = []
            for monitor in monitors:
                left, top, right, bottom = monitor['bounds']
                try:
                    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
                    screenshots.append(np.array(screenshot))
                except Exception as e:
                    logger.warning(f"捕获显示器 {monitor['index']} 时出错: {e}")
            
            return screenshots
        
        except Exception as e:
            logger.error(f"捕获所有屏幕时出错: {e}")
            # 尝试使用备用方法
            try:
                screenshot = ImageGrab.grab()
                return [np.array(screenshot)]
            except Exception as e2:
                logger.error(f"备用截图方法也失败: {e2}")
                return []
    
    @staticmethod
    def capture_active_window():
        """
        捕获当前活动窗口，支持Windows 11特有的窗口类型
        
        Returns:
            numpy.ndarray: 活动窗口截图的numpy数组
        """
        try:
            # 检查截图权限
            if not check_screenshot_permission():
                logger.warning("缺少截图权限，尝试请求权限")
                if not request_screenshot_permission():
                    logger.error("用户拒绝授予截图权限")
                    show_permission_error("screenshot")
                    return None
            
            # 设置DPI感知
            Win11ScreenshotManager.set_process_dpi_awareness()
            
            # 获取活动窗口信息
            window_info = Win11WindowManager.get_active_window()
            if not window_info:
                logger.warning("无法获取活动窗口信息")
                return None
            
            # 获取窗口边界
            # 优先使用扩展边界（包括阴影和圆角）
            if window_info.get('extended_bounds'):
                left, top, right, bottom = window_info['extended_bounds']
            else:
                left, top = window_info['left'], window_info['top']
                right, bottom = left + window_info['width'], top + window_info['height']
            
            # 考虑DPI缩放
            dpi_scaling = window_info.get('dpi_scaling', 1.0)
            
            # 如果是Windows 11特有的窗口类型，使用特殊处理
            if window_info.get('is_win11_window'):
                # 对于Windows 11的现代应用和UWP应用，使用特殊的截图方法
                try:
                    # 尝试使用Windows 11特有的截图方法
                    return Win11ScreenshotManager._capture_modern_window(window_info)
                except Exception as e:
                    logger.warning(f"使用特殊方法捕获Windows 11窗口失败: {e}，回退到标准方法")
            
            # 标准截图方法
            # 调整边界以确保捕获完整窗口（包括圆角和阴影）
            # Windows 11窗口通常有圆角，需要稍微扩展边界
            padding = int(8 * dpi_scaling)  # 根据DPI缩放调整填充
            left = max(0, left - padding)
            top = max(0, top - padding)
            right += padding
            bottom += padding
            
            # 捕获窗口内容
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            
            return np.array(screenshot)
        
        except Exception as e:
            logger.error(f"捕获活动窗口时出错: {e}")
            return None
    
    @staticmethod
    def _capture_modern_window(window_info):
        """
        捕获Windows 11现代应用窗口（UWP、Store应用等）
        
        Args:
            window_info: 窗口信息字典
            
        Returns:
            numpy.ndarray: 窗口截图的numpy数组
        """
        try:
            hwnd = window_info['hwnd']
            
            # 获取窗口DC
            import win32gui
            import win32ui
            import win32con
            
            # 获取窗口尺寸
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            width = right - left
            height = bottom - top
            
            # 创建设备上下文
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # 创建位图对象
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # 复制窗口内容到位图
            # 使用SRCCOPY | CAPTUREBLT标志以确保捕获分层窗口
            result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)  # PW_RENDERFULLCONTENT = 2 | PW_CLIENTONLY = 1
            
            # 如果PrintWindow失败，尝试使用BitBlt
            if not result:
                save_dc.BitBlt((0, 0), (width, height), mfc_dc, (left, top), win32con.SRCCOPY)
            
            # 将位图转换为PIL图像
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            
            # 清理资源
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            # 转换为numpy数组
            return np.array(img)
        
        except Exception as e:
            logger.error(f"捕获现代窗口时出错: {e}")
            
            # 回退到标准方法
            left, top = window_info['left'], window_info['top']
            width, height = window_info['width'], window_info['height']
            screenshot = ImageGrab.grab(bbox=(left, top, left + width, top + height))
            return np.array(screenshot)
    
    @staticmethod
    def get_monitor_info():
        """
        获取所有显示器的信息
        
        Returns:
            list: 包含显示器信息的字典列表
        """
        try:
            # 定义MonitorEnumProc回调函数
            def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
                monitors.append({
                    'handle': hMonitor,
                    'bounds': (lprcMonitor.contents.left, lprcMonitor.contents.top,
                              lprcMonitor.contents.right, lprcMonitor.contents.bottom),
                    'index': len(monitors)
                })
                return True
            
            # 定义RECT结构体
            class RECT(Structure):
                _fields_ = [
                    ('left', c_int),
                    ('top', c_int),
                    ('right', c_int),
                    ('bottom', c_int)
                ]
            
            # 定义回调函数类型
            from ctypes import WINFUNCTYPE, POINTER
            MonitorEnumProc = WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, POINTER(RECT), ctypes.c_ulong)
            
            # 枚举所有显示器
            monitors = []
            windll.user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(monitor_enum_proc), 0)
            
            # 获取每个显示器的DPI信息
            for monitor in monitors:
                try:
                    # 获取显示器DPI
                    dpi_x, dpi_y = c_int(), c_int()
                    windll.shcore.GetDpiForMonitor(monitor['handle'], 0, byref(dpi_x), byref(dpi_y))
                    monitor['dpi_x'] = dpi_x.value
                    monitor['dpi_y'] = dpi_y.value
                    monitor['dpi_scaling'] = dpi_x.value / 96.0
                except Exception:
                    monitor['dpi_x'] = 96
                    monitor['dpi_y'] = 96
                    monitor['dpi_scaling'] = 1.0
            
            return monitors
        
        except Exception as e:
            logger.error(f"获取显示器信息时出错: {e}")
            return []

# 导出便捷函数
capture_screen = Win11ScreenshotManager.capture_screen
capture_all_screens = Win11ScreenshotManager.capture_all_screens
capture_active_window = Win11ScreenshotManager.capture_active_window

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试DPI感知设置
    Win11ScreenshotManager.set_process_dpi_awareness()
    
    # 测试获取显示器信息
    monitors = Win11ScreenshotManager.get_monitor_info()
    print(f"检测到 {len(monitors)} 个显示器:")
    for monitor in monitors:
        print(f"  显示器 {monitor['index']}: {monitor['bounds']}, DPI缩放: {monitor.get('dpi_scaling', 1.0)}")
    
    # 测试捕获活动窗口
    window_screenshot = Win11ScreenshotManager.capture_active_window()
    if window_screenshot is not None:
        print(f"活动窗口截图尺寸: {window_screenshot.shape}")
        
        # 保存截图用于测试
        Image.fromarray(window_screenshot).save("active_window_screenshot.png")
        print("已保存活动窗口截图到 active_window_screenshot.png")