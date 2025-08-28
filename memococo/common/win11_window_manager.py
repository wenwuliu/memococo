"""
Windows 11窗口管理模块

提供Windows 11特定的窗口管理功能，包括获取活动窗口信息、窗口标题和应用程序名称
"""

import os
import sys
import logging
import ctypes
from ctypes import windll, byref, create_unicode_buffer, sizeof
import psutil

# 导入Windows API相关模块
try:
    import win32gui
    import win32process
    import win32api
    import win32con
    import win32ui
    from win32com.client import Dispatch
except ImportError:
    raise ImportError("缺少必要的Windows API模块。请安装pywin32: pip install pywin32")

# 创建日志记录器
logger = logging.getLogger("win11_window_manager")

# Windows 11特有的窗口类名前缀
WIN11_WINDOW_CLASS_PREFIXES = [
    "Windows.UI.Core.CoreWindow",  # UWP应用
    "ApplicationFrameWindow",      # 现代应用
    "XAML_WindowedPopupClass"      # XAML弹出窗口
]

# Windows 11 DWM API常量
DWMWA_CLOAKED = 14
DWMWA_EXTENDED_FRAME_BOUNDS = 9

class Win11WindowManager:
    """Windows 11窗口管理类，提供获取窗口信息的方法"""
    
    @staticmethod
    def is_win11_window(hwnd):
        """
        检查窗口是否为Windows 11特有的窗口类型
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            bool: 如果是Windows 11特有窗口则返回True
        """
        try:
            class_name = win32gui.GetClassName(hwnd)
            return any(class_name.startswith(prefix) for prefix in WIN11_WINDOW_CLASS_PREFIXES)
        except Exception as e:
            logger.warning(f"检查窗口类型时出错: {e}")
            return False
    
    @staticmethod
    def get_active_window():
        """
        获取当前活动窗口的句柄和信息
        
        Returns:
            dict: 包含窗口信息的字典，如果获取失败则返回None
        """
        try:
            # 获取前台窗口句柄
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                logger.warning("无法获取活动窗口句柄")
                return None
            
            # 获取窗口矩形
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            
            # 获取窗口DPI缩放信息
            dpi_scaling = Win11WindowManager.get_window_dpi_scaling(hwnd)
            
            # 获取窗口扩展边界（考虑阴影和圆角）
            extended_bounds = Win11WindowManager.get_extended_frame_bounds(hwnd)
            
            # 获取窗口标题
            title = win32gui.GetWindowText(hwnd)
            
            # 获取窗口类名
            class_name = win32gui.GetClassName(hwnd)
            
            # 获取进程ID和可执行文件路径
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                exe_path = process.exe()
            except Exception as e:
                logger.warning(f"获取进程信息时出错: {e}")
                exe_path = None
            
            # 获取应用程序友好名称
            app_name = Win11WindowManager.get_friendly_app_name(exe_path) if exe_path else None
            
            # 检查是否为Windows 11特有窗口
            is_win11_window = Win11WindowManager.is_win11_window(hwnd)
            
            # 构建窗口信息字典
            window_info = {
                'hwnd': hwnd,
                'rect': rect,
                'left': left,
                'top': top,
                'width': width,
                'height': height,
                'title': title,
                'class_name': class_name,
                'pid': pid,
                'exe_path': exe_path,
                'app_name': app_name,
                'is_win11_window': is_win11_window,
                'dpi_scaling': dpi_scaling,
                'extended_bounds': extended_bounds
            }
            
            logger.debug(f"获取到活动窗口信息: {window_info}")
            return window_info
        
        except Exception as e:
            logger.error(f"获取活动窗口信息时出错: {e}")
            return None
    
    @staticmethod
    def get_window_dpi_scaling(hwnd):
        """
        获取窗口的DPI缩放因子
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            float: DPI缩放因子，默认为1.0
        """
        try:
            # 获取窗口所在显示器的DC
            monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
            dc = win32gui.GetDC(0)
            
            # 获取逻辑DPI和物理DPI
            logical_x = windll.gdi32.GetDeviceCaps(dc, win32con.LOGPIXELSX)
            physical_x = windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
            
            # 释放DC
            win32gui.ReleaseDC(0, dc)
            
            # 计算DPI缩放因子
            if physical_x > 0:
                dpi_scaling = logical_x / 96.0  # 96 DPI是标准DPI
                return dpi_scaling
            
            return 1.0  # 默认缩放因子
        
        except Exception as e:
            logger.warning(f"获取DPI缩放因子时出错: {e}")
            return 1.0
    
    @staticmethod
    def get_extended_frame_bounds(hwnd):
        """
        获取窗口的扩展边界（包括阴影和圆角）
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            tuple: (left, top, right, bottom)，如果获取失败则返回None
        """
        try:
            # 创建RECT结构体
            rect = ctypes.wintypes.RECT()
            
            # 调用DwmGetWindowAttribute获取扩展边界
            result = windll.dwmapi.DwmGetWindowAttribute(
                hwnd,
                DWMWA_EXTENDED_FRAME_BOUNDS,
                byref(rect),
                sizeof(rect)
            )
            
            if result == 0:  # S_OK
                return (rect.left, rect.top, rect.right, rect.bottom)
            
            return None
        
        except Exception as e:
            logger.warning(f"获取窗口扩展边界时出错: {e}")
            return None
    
    @staticmethod
    def get_friendly_app_name(exe_path):
        """
        获取应用程序的友好名称，优化支持Windows 11应用
        
        Args:
            exe_path: 可执行文件路径
            
        Returns:
            str: 应用程序友好名称
        """
        if not exe_path:
            return None
        
        try:
            # 检查是否为Windows Store应用或UWP应用
            if "WindowsApps" in exe_path:
                return Win11WindowManager._get_store_app_name(exe_path)
            
            # 尝试从文件版本信息获取
            try:
                info = win32api.GetFileVersionInfo(exe_path, "\\")
                
                # 获取文件描述
                try:
                    lang, codepage = win32api.GetFileVersionInfo(exe_path, '\\VarFileInfo\\Translation')[0]
                    
                    # 尝试获取产品名称（通常更友好）
                    try:
                        product_name_path = f'\\StringFileInfo\\{lang:04x}{codepage:04x}\\ProductName'
                        product_name = win32api.GetFileVersionInfo(exe_path, product_name_path)
                        if product_name and len(product_name.strip()) > 0:
                            return product_name
                    except:
                        pass
                    
                    # 尝试获取文件描述
                    try:
                        file_desc_path = f'\\StringFileInfo\\{lang:04x}{codepage:04x}\\FileDescription'
                        file_desc = win32api.GetFileVersionInfo(exe_path, file_desc_path)
                        if file_desc and len(file_desc.strip()) > 0:
                            return file_desc
                    except:
                        pass
                except:
                    pass
            except:
                pass
            
            # 如果无法从版本信息获取，尝试从Shell获取
            try:
                shell = Dispatch("Shell.Application")
                folder = shell.Namespace(os.path.dirname(exe_path))
                file_item = folder.ParseName(os.path.basename(exe_path))
                name = file_item.Name
                if name and len(name.strip()) > 0:
                    return name
            except:
                pass
            
            # 如果以上方法都失败，返回文件名
            filename = os.path.splitext(os.path.basename(exe_path))[0]
            
            # 美化文件名（移除下划线、连字符等）
            filename = filename.replace("_", " ").replace("-", " ")
            filename = " ".join(word.capitalize() for word in filename.split())
            
            return filename
        
        except Exception as e:
            logger.warning(f"获取应用程序友好名称时出错: {e}")
            return os.path.splitext(os.path.basename(exe_path))[0]
    
    @staticmethod
    def _get_store_app_name(exe_path):
        """
        获取Windows Store应用或UWP应用的友好名称
        
        Args:
            exe_path: 可执行文件路径
            
        Returns:
            str: 应用程序友好名称
        """
        try:
            # 从路径中提取应用ID
            # 典型的Windows Store应用路径格式:
            # C:\Program Files\WindowsApps\Microsoft.WindowsCalculator_11.2210.0.0_x64__8wekyb3d8bbwe\Calculator.exe
            parts = exe_path.split('\\')
            app_id_index = -1
            
            for i, part in enumerate(parts):
                if "WindowsApps" in part:
                    app_id_index = i + 1
                    break
            
            if app_id_index >= 0 and app_id_index < len(parts):
                app_id = parts[app_id_index]
                
                # 从应用ID中提取应用名称
                # 格式通常是: Publisher.AppName_Version_Architecture__PublisherId
                app_parts = app_id.split('_')
                if len(app_parts) > 0:
                    publisher_app = app_parts[0]
                    if "." in publisher_app:
                        app_name = publisher_app.split('.', 1)[1]
                        
                        # 美化应用名称
                        app_name = app_name.replace(".", " ")
                        words = []
                        current_word = ""
                        
                        # 处理驼峰命名法
                        for char in app_name:
                            if char.isupper() and current_word:
                                words.append(current_word)
                                current_word = char
                            else:
                                current_word += char
                        
                        if current_word:
                            words.append(current_word)
                        
                        friendly_name = " ".join(words)
                        return friendly_name
            
            # 如果无法从路径提取，尝试使用文件名
            filename = os.path.splitext(os.path.basename(exe_path))[0]
            return filename
        
        except Exception as e:
            logger.warning(f"获取Store应用名称时出错: {e}")
            return os.path.splitext(os.path.basename(exe_path))[0]
    
    @staticmethod
    def get_app_name_mapping():
        """
        获取常见Windows 11应用的名称映射
        
        Returns:
            dict: 应用程序名称映射字典
        """
        return {
            # Windows 11系统应用
            "explorer.exe": "File Explorer",
            "msedge.exe": "Microsoft Edge",
            "ApplicationFrameHost.exe": "Windows App",
            "SystemSettings.exe": "Settings",
            "WindowsTerminal.exe": "Terminal",
            "SearchHost.exe": "Search",
            "StartMenuExperienceHost.exe": "Start Menu",
            "ShellExperienceHost.exe": "Shell Experience",
            "Widgets.exe": "Widgets",
            "ScreenClippingHost.exe": "Snipping Tool",
            "LockApp.exe": "Lock Screen",
            "WinStore.App.exe": "Microsoft Store",
            
            # 常见第三方应用
            "chrome.exe": "Google Chrome",
            "firefox.exe": "Mozilla Firefox",
            "Code.exe": "Visual Studio Code",
            "Teams.exe": "Microsoft Teams",
            "Slack.exe": "Slack",
            "Discord.exe": "Discord",
            "Spotify.exe": "Spotify",
            "Zoom.exe": "Zoom",
            "Telegram.exe": "Telegram",
            "WhatsApp.exe": "WhatsApp",
            "Skype.exe": "Skype",
            "Outlook.exe": "Microsoft Outlook",
            "Excel.exe": "Microsoft Excel",
            "Word.exe": "Microsoft Word",
            "PowerPoint.exe": "Microsoft PowerPoint",
            "OneNote.exe": "Microsoft OneNote",
            "Photoshop.exe": "Adobe Photoshop",
            "Illustrator.exe": "Adobe Illustrator",
            "AcroRd32.exe": "Adobe Reader",
            "Acrobat.exe": "Adobe Acrobat",
            "vlc.exe": "VLC Media Player",
            "notepad.exe": "Notepad",
            "notepad++.exe": "Notepad++",
            "mspaint.exe": "Paint",
            "calc.exe": "Calculator"
        }
    
    @staticmethod
    def get_window_title(hwnd=None):
        """
        获取窗口标题
        
        Args:
            hwnd: 窗口句柄，如果为None则获取活动窗口
            
        Returns:
            str: 窗口标题
        """
        try:
            if hwnd is None:
                hwnd = win32gui.GetForegroundWindow()
            
            return win32gui.GetWindowText(hwnd)
        
        except Exception as e:
            logger.warning(f"获取窗口标题时出错: {e}")
            return ""
    
    @staticmethod
    def get_active_app_name():
        """
        获取当前活动窗口的应用程序名称
        
        Returns:
            str: 应用程序名称
        """
        window_info = Win11WindowManager.get_active_window()
        if window_info and window_info.get('app_name'):
            return window_info['app_name']
        
        return ""
    
    @staticmethod
    def get_active_window_title():
        """
        获取当前活动窗口的标题
        
        Returns:
            str: 窗口标题
        """
        window_info = Win11WindowManager.get_active_window()
        if window_info and window_info.get('title'):
            return window_info['title']
        
        return ""

# 导出便捷函数
get_active_window = Win11WindowManager.get_active_window
get_active_app_name = Win11WindowManager.get_active_app_name
get_active_window_title = Win11WindowManager.get_active_window_title
get_window_title = Win11WindowManager.get_window_title

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试获取活动窗口信息
    window_info = Win11WindowManager.get_active_window()
    print(f"活动窗口信息: {window_info}")
    
    # 测试获取应用程序名称
    app_name = Win11WindowManager.get_active_app_name()
    print(f"应用程序名称: {app_name}")
    
    # 测试获取窗口标题
    title = Win11WindowManager.get_active_window_title()
    print(f"窗口标题: {title}")