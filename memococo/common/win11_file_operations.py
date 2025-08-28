"""
Windows 11文件操作模块

提供Windows 11特定的文件操作功能，优化文件读写性能
"""

import os
import sys
import logging
import csv
import io
import time
import datetime
from datetime import timedelta
import subprocess
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import cv2
from PIL import Image
import ctypes
from ctypes import windll, byref, c_int, Structure, sizeof, c_ulong, c_wchar_p, POINTER

# 创建日志记录器
logger = logging.getLogger("win11_file_operations")

# Windows 11文件操作相关常量
FILE_ATTRIBUTE_NORMAL = 0x80
FILE_FLAG_SEQUENTIAL_SCAN = 0x08000000
FILE_FLAG_OVERLAPPED = 0x40000000
FILE_FLAG_NO_BUFFERING = 0x20000000
FILE_FLAG_WRITE_THROUGH = 0x80000000
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
CREATE_ALWAYS = 2
OPEN_EXISTING = 3
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004

# 视频记录文件名
RECORD_NAME = "record.mp4"

class Win11FileOperations:
    """Windows 11文件操作类，提供优化的文件读写功能"""
    
    @staticmethod
    def read_file_fast(file_path, buffer_size=4096):
        """
        使用Windows API快速读取文件
        
        Args:
            file_path: 文件路径
            buffer_size: 缓冲区大小
            
        Returns:
            bytes: 文件内容
        """
        try:
            # 使用Python内置函数读取小文件
            if os.path.getsize(file_path) < 1024 * 1024:  # 小于1MB
                with open(file_path, 'rb') as f:
                    return f.read()
            
            # 对于大文件，使用Windows API
            h_file = windll.kernel32.CreateFileW(
                file_path,
                GENERIC_READ,
                FILE_SHARE_READ,
                None,
                OPEN_EXISTING,
                FILE_ATTRIBUTE_NORMAL | FILE_FLAG_SEQUENTIAL_SCAN,
                None
            )
            
            if h_file == -1:  # INVALID_HANDLE_VALUE
                raise IOError(f"无法打开文件: {file_path}")
            
            try:
                # 获取文件大小
                file_size = windll.kernel32.GetFileSize(h_file, None)
                
                # 分配缓冲区
                buffer = bytearray(file_size)
                bytes_read = c_ulong(0)
                
                # 读取文件
                result = windll.kernel32.ReadFile(
                    h_file,
                    buffer,
                    file_size,
                    byref(bytes_read),
                    None
                )
                
                if not result or bytes_read.value != file_size:
                    raise IOError(f"读取文件失败: {file_path}")
                
                return bytes(buffer)
            
            finally:
                windll.kernel32.CloseHandle(h_file)
        
        except Exception as e:
            logger.error(f"快速读取文件时出错: {e}")
            # 回退到标准方法
            with open(file_path, 'rb') as f:
                return f.read()
    
    @staticmethod
    def write_file_fast(file_path, data):
        """
        使用Windows API快速写入文件
        
        Args:
            file_path: 文件路径
            data: 要写入的数据
            
        Returns:
            bool: 如果成功写入则返回True
        """
        try:
            # 使用Python内置函数写入小文件
            if len(data) < 1024 * 1024:  # 小于1MB
                with open(file_path, 'wb') as f:
                    f.write(data)
                return True
            
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # 对于大文件，使用Windows API
            h_file = windll.kernel32.CreateFileW(
                file_path,
                GENERIC_WRITE,
                0,  # 不共享
                None,
                CREATE_ALWAYS,
                FILE_ATTRIBUTE_NORMAL | FILE_FLAG_WRITE_THROUGH,
                None
            )
            
            if h_file == -1:  # INVALID_HANDLE_VALUE
                raise IOError(f"无法创建文件: {file_path}")
            
            try:
                # 写入文件
                bytes_written = c_ulong(0)
                result = windll.kernel32.WriteFile(
                    h_file,
                    data,
                    len(data),
                    byref(bytes_written),
                    None
                )
                
                if not result or bytes_written.value != len(data):
                    raise IOError(f"写入文件失败: {file_path}")
                
                return True
            
            finally:
                windll.kernel32.CloseHandle(h_file)
        
        except Exception as e:
            logger.error(f"快速写入文件时出错: {e}")
            # 回退到标准方法
            with open(file_path, 'wb') as f:
                f.write(data)
            return True
    
    @staticmethod
    def get_file_attributes(file_path):
        """
        获取文件属性
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 文件属性字典
        """
        try:
            # 获取基本文件信息
            stat_info = os.stat(file_path)
            
            # 获取文件创建时间、修改时间和访问时间
            creation_time = datetime.datetime.fromtimestamp(stat_info.st_ctime)
            modification_time = datetime.datetime.fromtimestamp(stat_info.st_mtime)
            access_time = datetime.datetime.fromtimestamp(stat_info.st_atime)
            
            # 获取文件大小
            file_size = stat_info.st_size
            
            # 获取文件类型
            _, file_extension = os.path.splitext(file_path)
            
            # 构建属性字典
            attributes = {
                'path': file_path,
                'size': file_size,
                'size_human': Win11FileOperations.format_file_size(file_size),
                'creation_time': creation_time,
                'modification_time': modification_time,
                'access_time': access_time,
                'extension': file_extension.lower(),
                'is_hidden': bool(stat_info.st_file_attributes & 0x2) if hasattr(stat_info, 'st_file_attributes') else False,
                'is_system': bool(stat_info.st_file_attributes & 0x4) if hasattr(stat_info, 'st_file_attributes') else False,
                'is_archive': bool(stat_info.st_file_attributes & 0x20) if hasattr(stat_info, 'st_file_attributes') else False,
            }
            
            return attributes
        
        except Exception as e:
            logger.error(f"获取文件属性时出错: {e}")
            return {
                'path': file_path,
                'error': str(e)
            }
    
    @staticmethod
    def format_file_size(size_bytes):
        """
        格式化文件大小
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            str: 格式化后的文件大小
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    @staticmethod
    def get_folder_size(folder_path):
        """
        获取文件夹大小
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            int: 文件夹大小（字节）
        """
        try:
            total_size = 0
            
            # 使用os.walk遍历文件夹
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            
            return total_size
        
        except Exception as e:
            logger.error(f"获取文件夹大小时出错: {e}")
            return 0
    
    @staticmethod
    def format_folder_size(folder_path):
        """
        获取并格式化文件夹大小
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            str: 格式化后的文件夹大小
        """
        size_bytes = Win11FileOperations.get_folder_size(folder_path)
        return Win11FileOperations.format_file_size(size_bytes)

class Win11ImageVideoTool:
    """Windows 11图像视频工具类，提供优化的图像和视频处理功能"""
    
    def __init__(self,
                 image_folder: str,
                 output_video: str = RECORD_NAME,
                 framerate: int = 30,
                 crf: int = 23,
                 resolution: Optional[str] = None):
        """
        初始化图像视频工具
        
        Args:
            image_folder: 图像文件夹路径
            output_video: 输出视频文件名
            framerate: 帧率
            crf: 压缩质量
            resolution: 分辨率
        """
        self.image_folder = image_folder
        self.output_video = os.path.join(self.image_folder, output_video)
        self.framerate = framerate
        self.crf = crf
        self.resolution = resolution
        self.mapping_file = os.path.join(self.image_folder, f"{output_video}.csv")
        
        # 确保目录存在
        os.makedirs(self.image_folder, exist_ok=True)
        
        # 初始化视频捕获对象
        self.cap = None
        self.max_frame_num = 0
        self._init_video_capture()
    
    def _init_video_capture(self):
        """初始化视频捕获对象"""
        try:
            if os.path.exists(self.output_video):
                self.cap = cv2.VideoCapture(self.output_video)
                self.max_frame_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            else:
                self.cap = None
                self.max_frame_num = 0
        except Exception as e:
            logger.error(f"初始化视频捕获对象时出错: {e}")
            self.cap = None
            self.max_frame_num = 0
    
    def is_backed_up(self):
        """
        检查是否已备份
        
        Returns:
            bool: 如果已备份则返回True
        """
        return os.path.exists(self.mapping_file) and os.path.exists(self.output_video)
    
    def get_image_count(self):
        """
        获取图像数量
        
        Returns:
            int: 图像数量
        """
        try:
            # 只计算图像文件
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']
            count = sum(1 for file in os.listdir(self.image_folder) 
                      if os.path.isfile(os.path.join(self.image_folder, file)) and 
                      any(file.lower().endswith(ext) for ext in image_extensions))
            return count
        except Exception as e:
            logger.error(f"获取图像数量时出错: {e}")
            return 0
    
    def get_folder_size(self):
        """
        获取文件夹大小
        
        Returns:
            str: 格式化后的文件夹大小
        """
        return Win11FileOperations.format_folder_size(self.image_folder)
    
    def images_to_video(self,
                        sort_by: str = "name",
                        image_extensions: List[str] = [".jpg", ".jpeg", ".png", ".webp"]):
        """
        将图像转换为视频
        
        Args:
            sort_by: 排序方式
            image_extensions: 图像扩展名列表
        """
        try:
            # 收集并过滤图像
            images = []
            for file in os.listdir(self.image_folder):
                file_path = os.path.join(self.image_folder, file)
                if (os.path.isfile(file_path) and 
                    any(file.lower().endswith(ext) for ext in image_extensions)):
                    # 检查文件大小
                    if os.path.getsize(file_path) > 0:
                        images.append(file)
                    else:
                        # 删除空文件
                        os.remove(file_path)
            
            if not images:
                logger.warning(f"文件夹中没有有效图像: {self.image_folder}")
                return
            
            # 排序图像
            if sort_by == "name":
                images = sorted(images)
            elif sort_by == "time":
                images = sorted(images, key=lambda x: os.path.getmtime(os.path.join(self.image_folder, x)))
            else:
                raise ValueError(f"不支持的排序方式: {sort_by}")
            
            # 重命名图像
            renamed_images = []
            for idx, img in enumerate(images):
                old_path = os.path.join(self.image_folder, img)
                new_filename = f"{idx + 1:03d}.webp"
                new_path = os.path.join(self.image_folder, new_filename)
                os.rename(old_path, new_path)
                renamed_images.append(new_filename)
            
            # 生成映射表
            with open(self.mapping_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "timestamp", "frame_number"])
                for idx, img in enumerate(images):
                    timestamp = timedelta(seconds=idx/self.framerate)
                    writer.writerow([img, str(timestamp), idx+1])
            
            # 生成视频
            command = [
                "ffmpeg",
                "-framerate", f"{self.framerate}",
                "-i", os.path.join(self.image_folder, "%03d.webp"),
                "-c:v", "h264",
                "-crf", f"{self.crf}",
                "-preset", "medium",
                "-y", self.output_video
            ]
            
            # 如果指定了分辨率，添加分辨率参数
            if self.resolution:
                command.extend(["-s", self.resolution])
            
            # 执行命令
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            # 删除重命名后的图像
            for img in renamed_images:
                os.remove(os.path.join(self.image_folder, img))
            
            # 重新初始化视频捕获对象
            self._init_video_capture()
            
            logger.info(f"视频创建成功: {self.output_video}, 映射保存到: {self.mapping_file}")
        
        except Exception as e:
            logger.error(f"将图像转换为视频时出错: {e}")
            raise
    
    def query_image(self, target_image: str):
        """
        查询图像
        
        Args:
            target_image: 目标图像名称或时间戳
            
        Returns:
            io.BytesIO: 图像字节流
        """
        try:
            # 检查是否已备份
            if not self.is_backed_up():
                logger.warning(f"未备份: {self.image_folder}")
                return None
            
            # 读取映射表
            mapping = {}
            with open(self.mapping_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mapping[row["filename"]] = {
                        "timestamp": row["timestamp"],
                        "frame_number": row["frame_number"]
                    }
            
            # 模糊匹配
            matches = [k for k in mapping.keys() if target_image in k]
            if not matches:
                logger.warning(f"未找到匹配项: {target_image}")
                return None
            
            if len(matches) > 1:
                logger.warning(f"找到多个匹配项: {matches}，使用第一个")
            
            target = matches[0]
            frame_num = int(mapping[target]["frame_number"])
            
            # 检查视频捕获对象
            if self.cap is None or not self.cap.isOpened():
                self._init_video_capture()
                if self.cap is None or not self.cap.isOpened():
                    logger.error(f"无法打开视频: {self.output_video}")
                    return None
            
            # 提取帧
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num - 1)
            ret, frame = self.cap.read()
            
            if not ret:
                logger.error(f"无法读取帧: {frame_num}")
                return None
            
            # 编码为JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            byte_stream = io.BytesIO(buffer.tobytes())
            
            return byte_stream
        
        except Exception as e:
            logger.error(f"查询图像时出错: {e}")
            return None

# Windows 11数据备份与恢复类
class Win11DataBackup:
    """Windows 11数据备份与恢复类，提供与Windows 11备份机制集成的功能"""
    
    @staticmethod
    def backup_folder(source_folder, backup_folder=None, compress=True):
        """
        备份文件夹
        
        Args:
            source_folder: 源文件夹路径
            backup_folder: 备份文件夹路径，如果为None则使用默认路径
            compress: 是否压缩
            
        Returns:
            str: 备份文件夹路径
        """
        try:
            # 如果未指定备份文件夹，使用默认路径
            if backup_folder is None:
                # 获取Windows 11备份文件夹
                from memococo.common.win11_data_storage import get_documents_folder
                backup_root = get_documents_folder("MemoCoco_Backups")
                
                # 创建时间戳子文件夹
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_folder = os.path.join(backup_root, f"backup_{timestamp}")
            
            # 确保备份文件夹存在
            os.makedirs(backup_folder, exist_ok=True)
            
            # 如果需要压缩，使用ZIP格式
            if compress:
                import zipfile
                
                # 创建ZIP文件路径
                zip_path = f"{backup_folder}.zip"
                
                # 创建ZIP文件
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # 遍历源文件夹
                    for root, _, files in os.walk(source_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # 计算相对路径
                            rel_path = os.path.relpath(file_path, source_folder)
                            # 添加到ZIP文件
                            zipf.write(file_path, rel_path)
                
                logger.info(f"已创建压缩备份: {zip_path}")
                return zip_path
            
            # 否则，使用文件复制
            else:
                import shutil
                
                # 复制文件夹
                shutil.copytree(source_folder, backup_folder)
                
                logger.info(f"已创建备份: {backup_folder}")
                return backup_folder
        
        except Exception as e:
            logger.error(f"备份文件夹时出错: {e}")
            return None
    
    @staticmethod
    def restore_backup(backup_path, restore_folder):
        """
        恢复备份
        
        Args:
            backup_path: 备份路径（文件夹或ZIP文件）
            restore_folder: 恢复目标文件夹
            
        Returns:
            bool: 如果成功恢复则返回True
        """
        try:
            # 检查备份路径是否为ZIP文件
            if backup_path.endswith('.zip'):
                import zipfile
                
                # 确保恢复文件夹存在
                os.makedirs(restore_folder, exist_ok=True)
                
                # 解压ZIP文件
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(restore_folder)
                
                logger.info(f"已从ZIP文件恢复备份: {backup_path} -> {restore_folder}")
                return True
            
            # 否则，假设是文件夹
            elif os.path.isdir(backup_path):
                import shutil
                
                # 如果恢复文件夹已存在，先删除
                if os.path.exists(restore_folder):
                    shutil.rmtree(restore_folder)
                
                # 复制文件夹
                shutil.copytree(backup_path, restore_folder)
                
                logger.info(f"已从文件夹恢复备份: {backup_path} -> {restore_folder}")
                return True
            
            else:
                logger.error(f"无效的备份路径: {backup_path}")
                return False
        
        except Exception as e:
            logger.error(f"恢复备份时出错: {e}")
            return False
    
    @staticmethod
    def list_backups(backup_root=None):
        """
        列出可用的备份
        
        Args:
            backup_root: 备份根目录，如果为None则使用默认路径
            
        Returns:
            list: 备份信息列表
        """
        try:
            # 如果未指定备份根目录，使用默认路径
            if backup_root is None:
                # 获取Windows 11备份文件夹
                from memococo.common.win11_data_storage import get_documents_folder
                backup_root = get_documents_folder("MemoCoco_Backups")
            
            # 如果备份根目录不存在，返回空列表
            if not os.path.exists(backup_root):
                return []
            
            backups = []
            
            # 查找ZIP文件
            for file in os.listdir(backup_root):
                file_path = os.path.join(backup_root, file)
                
                # 检查是否为ZIP文件
                if file.startswith("backup_") and file.endswith(".zip") and os.path.isfile(file_path):
                    # 提取时间戳
                    try:
                        timestamp_str = file[7:-4]  # 去掉"backup_"前缀和".zip"后缀
                        timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        
                        # 获取文件大小
                        size = os.path.getsize(file_path)
                        size_str = Win11FileOperations.format_file_size(size)
                        
                        # 添加到备份列表
                        backups.append({
                            'path': file_path,
                            'timestamp': timestamp,
                            'size': size,
                            'size_str': size_str,
                            'type': 'zip'
                        })
                    except ValueError:
                        # 忽略格式不正确的文件名
                        pass
            
            # 查找备份文件夹
            for folder in os.listdir(backup_root):
                folder_path = os.path.join(backup_root, folder)
                
                # 检查是否为文件夹且名称符合格式
                if folder.startswith("backup_") and os.path.isdir(folder_path):
                    # 提取时间戳
                    try:
                        timestamp_str = folder[7:]  # 去掉"backup_"前缀
                        timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        
                        # 获取文件夹大小
                        size = Win11FileOperations.get_folder_size(folder_path)
                        size_str = Win11FileOperations.format_file_size(size)
                        
                        # 添加到备份列表
                        backups.append({
                            'path': folder_path,
                            'timestamp': timestamp,
                            'size': size,
                            'size_str': size_str,
                            'type': 'folder'
                        })
                    except ValueError:
                        # 忽略格式不正确的文件夹名
                        pass
            
            # 按时间戳排序（最新的在前）
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return backups
        
        except Exception as e:
            logger.error(f"列出备份时出错: {e}")
            return []
    
    @staticmethod
    def create_scheduled_backup(source_folder, schedule="daily"):
        """
        创建计划备份任务
        
        Args:
            source_folder: 源文件夹路径
            schedule: 计划类型（"daily"、"weekly"或"monthly"）
            
        Returns:
            bool: 如果成功创建计划任务则返回True
        """
        try:
            # 获取应用程序路径
            import sys
            app_path = sys.executable
            
            # 构建备份命令
            script_path = os.path.abspath(__file__)
            backup_command = f'"{app_path}" "{script_path}" --backup "{source_folder}"'
            
            # 创建计划任务
            if schedule == "daily":
                task_time = "03:00"
                recurrence = "/SC DAILY"
            elif schedule == "weekly":
                task_time = "04:00"
                recurrence = "/SC WEEKLY /D SUN"
            elif schedule == "monthly":
                task_time = "05:00"
                recurrence = "/SC MONTHLY /D 1"
            else:
                raise ValueError(f"不支持的计划类型: {schedule}")
            
            # 构建计划任务命令
            task_name = f"MemoCoco_Backup_{os.path.basename(source_folder)}"
            schtasks_command = f'schtasks /Create /TN "{task_name}" /TR "{backup_command}" /ST {task_time} {recurrence} /F'
            
            # 执行命令
            result = subprocess.run(
                schtasks_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                logger.info(f"已创建计划备份任务: {task_name}")
                return True
            else:
                logger.error(f"创建计划备份任务失败: {result.stderr.decode()}")
                return False
        
        except Exception as e:
            logger.error(f"创建计划备份任务时出错: {e}")
            return False
    
    @staticmethod
    def remove_scheduled_backup(task_name=None, source_folder=None):
        """
        删除计划备份任务
        
        Args:
            task_name: 计划任务名称
            source_folder: 源文件夹路径
            
        Returns:
            bool: 如果成功删除计划任务则返回True
        """
        try:
            # 如果未指定任务名称但指定了源文件夹，构建任务名称
            if task_name is None and source_folder is not None:
                task_name = f"MemoCoco_Backup_{os.path.basename(source_folder)}"
            
            # 如果未指定任务名称，返回失败
            if task_name is None:
                logger.error("未指定计划任务名称")
                return False
            
            # 构建删除计划任务命令
            schtasks_command = f'schtasks /Delete /TN "{task_name}" /F'
            
            # 执行命令
            result = subprocess.run(
                schtasks_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                logger.info(f"已删除计划备份任务: {task_name}")
                return True
            else:
                logger.error(f"删除计划备份任务失败: {result.stderr.decode()}")
                return False
        
        except Exception as e:
            logger.error(f"删除计划备份任务时出错: {e}")
            return False

# 导出便捷函数
read_file_fast = Win11FileOperations.read_file_fast
write_file_fast = Win11FileOperations.write_file_fast
get_file_attributes = Win11FileOperations.get_file_attributes
get_folder_size = Win11FileOperations.get_folder_size
format_file_size = Win11FileOperations.format_file_size

# 导出备份与恢复函数
backup_folder = Win11DataBackup.backup_folder
restore_backup = Win11DataBackup.restore_backup
list_backups = Win11DataBackup.list_backups
create_scheduled_backup = Win11DataBackup.create_scheduled_backup
remove_scheduled_backup = Win11DataBackup.remove_scheduled_backup

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试文件操作
    test_file = "test.txt"
    test_data = b"Hello, Windows 11!"
    
    # 写入文件
    write_file_fast(test_file, test_data)
    
    # 读取文件
    read_data = read_file_fast(test_file)
    print(f"读取的数据: {read_data}")
    
    # 获取文件属性
    attributes = get_file_attributes(test_file)
    print(f"文件属性: {attributes}")
    
    # 清理
    os.remove(test_file)
    
    # 测试图像视频工具
    test_folder = "test_images"
    os.makedirs(test_folder, exist_ok=True)
    
    # 创建测试图像
    for i in range(5):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:, :, 0] = i * 50  # 蓝色通道
        cv2.imwrite(os.path.join(test_folder, f"image_{i}.png"), img)
    
    # 创建图像视频工具
    tool = Win11ImageVideoTool(test_folder)
    
    # 获取图像数量
    image_count = tool.get_image_count()
    print(f"图像数量: {image_count}")
    
    # 获取文件夹大小
    folder_size = tool.get_folder_size()
    print(f"文件夹大小: {folder_size}")
    
    # 将图像转换为视频
    tool.images_to_video(sort_by="name")
    
    # 查询图像
    image_stream = tool.query_image("image_0")
    if image_stream:
        print("成功查询图像")
    
    # 清理
    import shutil
    shutil.rmtree(test_folder)