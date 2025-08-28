"""
Windows 11权限管理模块

提供Windows 11特定的权限管理功能，包括截图权限和管理员权限
"""

import os
import sys
import logging
import ctypes
from ctypes import windll, byref, c_bool, c_int, Structure, sizeof, c_ulong, POINTER
import tkinter as tk
from tkinter import messagebox

# 创建日志记录器
logger = logging.getLogger("win11_permission_manager")

# Windows 11权限相关常量
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x00000020
TOKEN_QUERY = 0x00000008
SE_SHUTDOWN_NAME = "SeShutdownPrivilege"
SE_DEBUG_NAME = "SeDebugPrivilege"
SE_BACKUP_NAME = "SeBackupPrivilege"

class LUID(Structure):
    _fields_ = [
        ("LowPart", c_ulong),
        ("HighPart", c_ulong)
    ]

class LUID_AND_ATTRIBUTES(Structure):
    _fields_ = [
        ("Luid", LUID),
        ("Attributes", c_ulong)
    ]

class TOKEN_PRIVILEGES(Structure):
    _fields_ = [
        ("PrivilegeCount", c_ulong),
        ("Privileges", LUID_AND_ATTRIBUTES * 1)
    ]

class Win11PermissionManager:
    """Windows 11权限管理类，提供权限检查和请求功能"""
    
    @staticmethod
    def is_admin():
        """
        检查当前进程是否具有管理员权限
        
        Returns:
            bool: 如果具有管理员权限则返回True
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception as e:
            logger.error(f"检查管理员权限时出错: {e}")
            return False
    
    @staticmethod
    def request_admin_privileges():
        """
        请求管理员权限
        
        如果当前进程没有管理员权限，则尝试以管理员身份重新启动
        
        Returns:
            bool: 如果成功请求管理员权限则返回True
        """
        if Win11PermissionManager.is_admin():
            logger.debug("已具有管理员权限")
            return True
        
        try:
            # 获取当前可执行文件路径
            exe_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            
            # 构建命令行参数
            params = ' '.join([f'"{item}"' for item in sys.argv[1:]])
            
            # 使用ShellExecute以管理员身份启动
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                exe_path,
                f'"{script_path}" {params}',
                None,
                1  # SW_SHOWNORMAL
            )
            
            # 如果返回值大于32，则表示成功
            if ret > 32:
                logger.info("成功请求管理员权限，应用程序将以管理员身份重新启动")
                sys.exit(0)
                return True
            else:
                logger.warning(f"请求管理员权限失败，返回值: {ret}")
                return False
        
        except Exception as e:
            logger.error(f"请求管理员权限时出错: {e}")
            return False
    
    @staticmethod
    def enable_privilege(privilege_name):
        """
        启用指定的特权
        
        Args:
            privilege_name: 特权名称，如"SeDebugPrivilege"
            
        Returns:
            bool: 如果成功启用特权则返回True
        """
        try:
            # 打开当前进程令牌
            token = c_ulong()
            if not windll.advapi32.OpenProcessToken(
                windll.kernel32.GetCurrentProcess(),
                TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
                byref(token)
            ):
                logger.error("无法打开进程令牌")
                return False
            
            # 查找特权的LUID
            luid = LUID()
            if not windll.advapi32.LookupPrivilegeValueW(
                None,
                privilege_name,
                byref(luid)
            ):
                logger.error(f"无法查找特权: {privilege_name}")
                windll.kernel32.CloseHandle(token)
                return False
            
            # 设置特权
            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Privileges[0].Luid = luid
            tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
            
            if not windll.advapi32.AdjustTokenPrivileges(
                token,
                False,
                byref(tp),
                sizeof(TOKEN_PRIVILEGES),
                None,
                None
            ):
                logger.error(f"无法调整令牌特权: {privilege_name}")
                windll.kernel32.CloseHandle(token)
                return False
            
            # 检查是否成功启用特权
            if windll.kernel32.GetLastError() != 0:
                logger.error(f"启用特权失败: {privilege_name}")
                windll.kernel32.CloseHandle(token)
                return False
            
            # 关闭令牌句柄
            windll.kernel32.CloseHandle(token)
            logger.debug(f"成功启用特权: {privilege_name}")
            return True
        
        except Exception as e:
            logger.error(f"启用特权时出错: {e}")
            return False
    
    @staticmethod
    def check_screenshot_permission():
        """
        检查是否具有截图权限
        
        在Windows 11中，某些应用（如UWP应用）可能需要特殊权限才能截图
        
        Returns:
            bool: 如果具有截图权限则返回True
        """
        try:
            # 在Windows 11中，截图通常不需要特殊权限
            # 但对于某些受保护的应用，可能需要SeDebugPrivilege
            if Win11PermissionManager.enable_privilege(SE_DEBUG_NAME):
                logger.debug("已启用调试特权，可以截取受保护的应用")
                return True
            
            # 即使没有特殊权限，也可以尝试截图
            logger.debug("无法启用调试特权，但仍将尝试截图")
            return True
        
        except Exception as e:
            logger.error(f"检查截图权限时出错: {e}")
            return True  # 默认允许尝试截图
    
    @staticmethod
    def request_screenshot_permission():
        """
        请求截图权限
        
        在Windows 11中，可能需要向用户显示权限请求对话框
        
        Returns:
            bool: 如果用户授予权限则返回True
        """
        try:
            # 检查是否已有截图权限
            if Win11PermissionManager.check_screenshot_permission():
                return True
            
            # 如果没有管理员权限，可能需要请求
            if not Win11PermissionManager.is_admin():
                # 创建一个隐藏的根窗口
                root = tk.Tk()
                root.withdraw()
                
                # 显示权限请求对话框
                result = messagebox.askyesno(
                    "需要权限",
                    "MemoCoco需要管理员权限才能捕获某些Windows 11应用的屏幕内容。\n\n"
                    "是否以管理员身份重新启动应用程序？"
                )
                
                # 销毁窗口
                root.destroy()
                
                if result:
                    # 用户同意，请求管理员权限
                    return Win11PermissionManager.request_admin_privileges()
                else:
                    # 用户拒绝，继续但可能无法捕获某些应用
                    logger.warning("用户拒绝授予管理员权限，某些应用可能无法捕获")
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"请求截图权限时出错: {e}")
            return False
    
    @staticmethod
    def show_permission_error(error_type="screenshot"):
        """
        显示权限错误消息
        
        Args:
            error_type: 错误类型，如"screenshot"或"admin"
        """
        try:
            # 创建一个隐藏的根窗口
            root = tk.Tk()
            root.withdraw()
            
            # 根据错误类型显示不同的消息
            if error_type == "screenshot":
                messagebox.showerror(
                    "权限错误",
                    "MemoCoco无法捕获屏幕内容。\n\n"
                    "这可能是因为缺少必要的权限。请尝试以管理员身份运行应用程序。"
                )
            elif error_type == "admin":
                messagebox.showerror(
                    "权限错误",
                    "MemoCoco需要管理员权限才能执行此操作。\n\n"
                    "请以管理员身份运行应用程序。"
                )
            else:
                messagebox.showerror(
                    "权限错误",
                    f"MemoCoco遇到权限问题: {error_type}\n\n"
                    "请检查应用程序权限设置。"
                )
            
            # 销毁窗口
            root.destroy()
        
        except Exception as e:
            logger.error(f"显示权限错误消息时出错: {e}")
            # 如果GUI显示失败，则打印到控制台
            print(f"权限错误: {error_type}")

# 导出便捷函数
is_admin = Win11PermissionManager.is_admin
request_admin_privileges = Win11PermissionManager.request_admin_privileges
check_screenshot_permission = Win11PermissionManager.check_screenshot_permission
request_screenshot_permission = Win11PermissionManager.request_screenshot_permission
show_permission_error = Win11PermissionManager.show_permission_error

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试管理员权限检查
    admin = Win11PermissionManager.is_admin()
    print(f"是否具有管理员权限: {admin}")
    
    # 测试截图权限检查
    screenshot_permission = Win11PermissionManager.check_screenshot_permission()
    print(f"是否具有截图权限: {screenshot_permission}")
    
    # 如果没有管理员权限，请求管理员权限
    if not admin:
        print("请求管理员权限...")
        Win11PermissionManager.request_admin_privileges()