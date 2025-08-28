"""
Windows 11数据存储模块

提供Windows 11特定的数据存储功能，包括应用数据路径和权限管理
"""

import os
import sys
import logging
import ctypes
from ctypes import windll, c_wchar_p, create_unicode_buffer, sizeof
import winreg

# 创建日志记录器
logger = logging.getLogger("win11_data_storage")

# Windows 11 FOLDERID常量
FOLDERID_LocalAppData = "{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}"
FOLDERID_RoamingAppData = "{3EB685DB-65F9-4CF6-A03A-E3EF65729F3D}"
FOLDERID_ProgramData = "{62AB5D82-FDC1-4DC3-A9DD-070D1D495D97}"

# SHGetKnownFolderPath函数参数
KF_FLAG_CREATE = 0x00008000
KF_FLAG_DONT_VERIFY = 0x00004000

class Win11DataStorage:
    """Windows 11数据存储类，提供数据存储路径和权限管理功能"""
    
    @staticmethod
    def get_known_folder_path(folder_id):
        """
        获取Windows已知文件夹的路径
        
        Args:
            folder_id: 文件夹ID，如FOLDERID_LocalAppData
            
        Returns:
            str: 文件夹路径，如果获取失败则返回None
        """
        try:
            # 定义SHGetKnownFolderPath函数
            SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
            SHGetKnownFolderPath.argtypes = [
                ctypes.c_void_p,  # rfid
                ctypes.c_uint32,  # dwFlags
                ctypes.c_void_p,  # hToken
                ctypes.POINTER(c_wchar_p)  # ppszPath
            ]
            
            # 创建GUID结构
            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", ctypes.c_ulong),
                    ("Data2", ctypes.c_ushort),
                    ("Data3", ctypes.c_ushort),
                    ("Data4", ctypes.c_ubyte * 8)
                ]
            
            # 解析GUID字符串
            guid = GUID()
            
            # 移除大括号并分割GUID字符串
            guid_str = folder_id.strip('{}')
            parts = guid_str.split('-')
            
            # 填充GUID结构
            guid.Data1 = int(parts[0], 16)
            guid.Data2 = int(parts[1], 16)
            guid.Data3 = int(parts[2], 16)
            guid.Data4[0] = int(parts[3][0:2], 16)
            guid.Data4[1] = int(parts[3][2:4], 16)
            for i in range(6):
                guid.Data4[i+2] = int(parts[4][i*2:i*2+2], 16)
            
            # 调用SHGetKnownFolderPath函数
            path_ptr = c_wchar_p()
            flags = KF_FLAG_CREATE | KF_FLAG_DONT_VERIFY
            result = SHGetKnownFolderPath(ctypes.byref(guid), flags, None, ctypes.byref(path_ptr))
            
            if result == 0:  # S_OK
                path = path_ptr.value
                # 释放内存
                windll.ole32.CoTaskMemFree(path_ptr)
                return path
            
            return None
        
        except Exception as e:
            logger.error(f"获取已知文件夹路径时出错: {e}")
            return None
    
    @staticmethod
    def get_app_data_folder(app_name):
        """
        获取应用数据存储路径
        
        在Windows 11中，应用数据通常存储在以下位置：
        - 用户数据: %LOCALAPPDATA%\\{app_name} 或 %APPDATA%\\{app_name}
        - 共享数据: %PROGRAMDATA%\\{app_name}
        
        Args:
            app_name: 应用程序名称
            
        Returns:
            str: 应用数据存储路径
        """
        try:
            # 优先使用LocalAppData（本地应用数据）
            local_appdata = Win11DataStorage.get_known_folder_path(FOLDERID_LocalAppData)
            if local_appdata:
                app_data_path = os.path.join(local_appdata, app_name)
                logger.debug(f"使用LocalAppData路径: {app_data_path}")
                
                # 确保目录存在
                if not os.path.exists(app_data_path):
                    os.makedirs(app_data_path)
                
                return app_data_path
            
            # 如果LocalAppData不可用，尝试使用RoamingAppData
            roaming_appdata = Win11DataStorage.get_known_folder_path(FOLDERID_RoamingAppData)
            if roaming_appdata:
                app_data_path = os.path.join(roaming_appdata, app_name)
                logger.debug(f"使用RoamingAppData路径: {app_data_path}")
                
                # 确保目录存在
                if not os.path.exists(app_data_path):
                    os.makedirs(app_data_path)
                
                return app_data_path
            
            # 如果以上方法都失败，回退到传统方法
            appdata = os.environ.get("APPDATA")
            if not appdata:
                raise EnvironmentError("APPDATA环境变量未设置")
            
            app_data_path = os.path.join(appdata, app_name)
            logger.debug(f"使用传统APPDATA路径: {app_data_path}")
            
            # 确保目录存在
            if not os.path.exists(app_data_path):
                os.makedirs(app_data_path)
            
            return app_data_path
        
        except Exception as e:
            logger.error(f"获取应用数据存储路径时出错: {e}")
            # 如果所有方法都失败，使用当前目录
            app_data_path = os.path.join(os.getcwd(), f".{app_name}")
            
            # 确保目录存在
            if not os.path.exists(app_data_path):
                os.makedirs(app_data_path)
            
            logger.warning(f"回退到当前目录: {app_data_path}")
            return app_data_path
    
    @staticmethod
    def ensure_directory_permissions(path):
        """
        确保目录具有正确的权限
        
        Args:
            path: 目录路径
            
        Returns:
            bool: 如果成功设置权限则返回True
        """
        try:
            # 检查目录是否存在
            if not os.path.exists(path):
                os.makedirs(path)
            
            # 获取当前用户的SID
            import win32security
            import win32api
            
            # 获取当前用户名
            username = win32api.GetUserName()
            
            # 获取当前用户的SID
            user_sid, domain, account_type = win32security.LookupAccountName(None, username)
            
            # 获取当前用户的安全描述符
            security_descriptor = win32security.GetFileSecurity(
                path, win32security.DACL_SECURITY_INFORMATION
            )
            
            # 获取DACL
            dacl = security_descriptor.GetSecurityDescriptorDacl()
            
            # 添加完全控制权限
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                win32security.FILE_ALL_ACCESS,
                user_sid
            )
            
            # 设置新的DACL
            security_descriptor.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                path, win32security.DACL_SECURITY_INFORMATION, security_descriptor
            )
            
            logger.debug(f"成功设置目录权限: {path}")
            return True
        
        except Exception as e:
            logger.error(f"设置目录权限时出错: {e}")
            return False
    
    @staticmethod
    def get_program_data_folder(app_name):
        """
        获取程序数据存储路径（共享数据）
        
        Args:
            app_name: 应用程序名称
            
        Returns:
            str: 程序数据存储路径
        """
        try:
            # 使用ProgramData
            program_data = Win11DataStorage.get_known_folder_path(FOLDERID_ProgramData)
            if program_data:
                app_data_path = os.path.join(program_data, app_name)
                logger.debug(f"使用ProgramData路径: {app_data_path}")
                
                # 确保目录存在
                if not os.path.exists(app_data_path):
                    os.makedirs(app_data_path)
                
                return app_data_path
            
            # 如果ProgramData不可用，回退到传统方法
            program_data = os.environ.get("PROGRAMDATA")
            if not program_data:
                raise EnvironmentError("PROGRAMDATA环境变量未设置")
            
            app_data_path = os.path.join(program_data, app_name)
            logger.debug(f"使用传统PROGRAMDATA路径: {app_data_path}")
            
            # 确保目录存在
            if not os.path.exists(app_data_path):
                os.makedirs(app_data_path)
            
            return app_data_path
        
        except Exception as e:
            logger.error(f"获取程序数据存储路径时出错: {e}")
            # 如果所有方法都失败，使用当前目录
            app_data_path = os.path.join(os.getcwd(), f".{app_name}_data")
            
            # 确保目录存在
            if not os.path.exists(app_data_path):
                os.makedirs(app_data_path)
            
            logger.warning(f"回退到当前目录: {app_data_path}")
            return app_data_path
    
    @staticmethod
    def get_temp_folder(app_name):
        """
        获取临时文件存储路径
        
        Args:
            app_name: 应用程序名称
            
        Returns:
            str: 临时文件存储路径
        """
        try:
            # 使用系统临时目录
            temp_dir = os.environ.get("TEMP")
            if not temp_dir:
                temp_dir = os.environ.get("TMP")
            
            if not temp_dir:
                raise EnvironmentError("TEMP和TMP环境变量未设置")
            
            app_temp_path = os.path.join(temp_dir, app_name)
            logger.debug(f"使用临时目录: {app_temp_path}")
            
            # 确保目录存在
            if not os.path.exists(app_temp_path):
                os.makedirs(app_temp_path)
            
            return app_temp_path
        
        except Exception as e:
            logger.error(f"获取临时文件存储路径时出错: {e}")
            # 如果所有方法都失败，使用当前目录
            app_temp_path = os.path.join(os.getcwd(), f".{app_name}_temp")
            
            # 确保目录存在
            if not os.path.exists(app_temp_path):
                os.makedirs(app_temp_path)
            
            logger.warning(f"回退到当前目录: {app_temp_path}")
            return app_temp_path

# 导出便捷函数
get_app_data_folder = Win11DataStorage.get_app_data_folder
ensure_directory_permissions = Win11DataStorage.ensure_directory_permissions
get_program_data_folder = Win11DataStorage.get_program_data_folder
get_temp_folder = Win11DataStorage.get_temp_folder

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试获取应用数据存储路径
    app_data_path = Win11DataStorage.get_app_data_folder("MemoCoco")
    print(f"应用数据存储路径: {app_data_path}")
    
    # 测试获取程序数据存储路径
    program_data_path = Win11DataStorage.get_program_data_folder("MemoCoco")
    print(f"程序数据存储路径: {program_data_path}")
    
    # 测试获取临时文件存储路径
    temp_path = Win11DataStorage.get_temp_folder("MemoCoco")
    print(f"临时文件存储路径: {temp_path}")
    
    # 测试设置目录权限
    Win11DataStorage.ensure_directory_permissions(app_data_path)