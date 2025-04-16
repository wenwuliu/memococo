"""
配置管理模块

提供统一的配置管理功能，支持配置的读取、保存和验证
"""

import os
import sys
import json
import toml
import time
import threading
import logging
from typing import Dict, Any, Optional, List, Callable, Union
from memococo.common.error_handler import ConfigError, ConfigNotFoundError, ConfigParseError, ConfigValidationError

class ConfigValidator:
    """配置验证器类

    用于验证配置项是否符合要求
    """

    @staticmethod
    def validate_type(value: Any, expected_type: Union[type, List[type]], key: str = None) -> bool:
        """验证值的类型

        Args:
            value: 要验证的值
            expected_type: 期望的类型或类型列表
            key: 配置项键名，用于错误消息

        Returns:
            bool: 验证是否通过

        Raises:
            ConfigValidationError: 当验证失败时抛出
        """
        # 特殊处理布尔类型
        if expected_type == bool or (isinstance(expected_type, list) and bool in expected_type):
            # 如果值是字符串形式的布尔值，转换为布尔值
            if isinstance(value, str) and value.lower() in ['true', 'false']:
                return True  # 允许字符串形式的布尔值通过验证

        if isinstance(expected_type, list):
            if not any(isinstance(value, t) for t in expected_type):
                type_names = [t.__name__ for t in expected_type]
                error_msg = f"配置项{key if key else ''}类型错误: 期望{' 或 '.join(type_names)}, 实际为{type(value).__name__}"
                raise ConfigValidationError(error_msg, {"key": key, "value": value, "expected_type": str(expected_type)})
            return True
        else:
            if not isinstance(value, expected_type):
                error_msg = f"配置项{key if key else ''}类型错误: 期望{expected_type.__name__}, 实际为{type(value).__name__}"
                raise ConfigValidationError(error_msg, {"key": key, "value": value, "expected_type": str(expected_type)})
            return True

    @staticmethod
    def validate_range(value: Union[int, float], min_value: Union[int, float] = None, max_value: Union[int, float] = None, key: str = None) -> bool:
        """验证值的范围

        Args:
            value: 要验证的值
            min_value: 最小值，如果为None则不验证最小值
            max_value: 最大值，如果为None则不验证最大值
            key: 配置项键名，用于错误消息

        Returns:
            bool: 验证是否通过

        Raises:
            ConfigValidationError: 当验证失败时抛出
        """
        if min_value is not None and value < min_value:
            error_msg = f"配置项{key if key else ''}值过小: 最小值为{min_value}, 实际值为{value}"
            raise ConfigValidationError(error_msg, {"key": key, "value": value, "min_value": min_value})

        if max_value is not None and value > max_value:
            error_msg = f"配置项{key if key else ''}值过大: 最大值为{max_value}, 实际值为{value}"
            raise ConfigValidationError(error_msg, {"key": key, "value": value, "max_value": max_value})

        return True

    @staticmethod
    def validate_enum(value: Any, enum_values: List[Any], key: str = None) -> bool:
        """验证值是否在枚举列表中

        Args:
            value: 要验证的值
            enum_values: 枚举值列表
            key: 配置项键名，用于错误消息

        Returns:
            bool: 验证是否通过

        Raises:
            ConfigValidationError: 当验证失败时抛出
        """
        if value not in enum_values:
            error_msg = f"配置项{key if key else ''}值不在允许范围内: 允许值为{enum_values}, 实际值为{value}"
            raise ConfigValidationError(error_msg, {"key": key, "value": value, "enum_values": enum_values})
        return True

    @staticmethod
    def validate_string(value: str, min_length: int = None, max_length: int = None, pattern: str = None, key: str = None) -> bool:
        """验证字符串

        Args:
            value: 要验证的字符串
            min_length: 最小长度，如果为None则不验证最小长度
            max_length: 最大长度，如果为None则不验证最大长度
            pattern: 正则表达式模式，如果为None则不验证模式
            key: 配置项键名，用于错误消息

        Returns:
            bool: 验证是否通过

        Raises:
            ConfigValidationError: 当验证失败时抛出
        """
        # 验证类型
        ConfigValidator.validate_type(value, str, key)

        # 验证最小长度
        if min_length is not None and len(value) < min_length:
            error_msg = f"配置项{key if key else ''}字符串长度过短: 最小长度为{min_length}, 实际长度为{len(value)}"
            raise ConfigValidationError(error_msg, {"key": key, "value": value, "min_length": min_length})

        # 验证最大长度
        if max_length is not None and len(value) > max_length:
            error_msg = f"配置项{key if key else ''}字符串长度过长: 最大长度为{max_length}, 实际长度为{len(value)}"
            raise ConfigValidationError(error_msg, {"key": key, "value": value, "max_length": max_length})

        # 验证模式
        if pattern is not None:
            import re
            if not re.match(pattern, value):
                error_msg = f"配置项{key if key else ''}字符串不符合模式: 模式为{pattern}, 实际值为{value}"
                raise ConfigValidationError(error_msg, {"key": key, "value": value, "pattern": pattern})

        return True

class ConfigManager:
    """配置管理类

    提供配置的读取、保存、验证和热加载功能
    """

    def __init__(self, config_file: str, default_config: Dict[str, Any], schema: Dict[str, Dict[str, Any]] = None, logger: logging.Logger = None):
        """初始化配置管理器

        Args:
            config_file: 配置文件路径
            default_config: 默认配置
            schema: 配置模式，用于验证配置
            logger: 日志记录器
        """
        self.config_file = config_file
        self.default_config = default_config
        self.schema = schema or {}
        self.logger = logger
        self.config = self._load_config()
        self.last_modified_time = self._get_file_modified_time()
        self.watch_thread = None
        self.watch_interval = 5  # 默讥秒检查一次
        self.is_watching = False
        self.callbacks = []  # 配置变更回调函数列表

    def _get_file_modified_time(self) -> float:
        """获取文件修改时间

        Returns:
            float: 文件修改时间戳
        """
        try:
            if os.path.exists(self.config_file):
                return os.path.getmtime(self.config_file)
            return 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"获取文件修改时间失败: {self.config_file}, 错误: {e}")
            return 0

    def _load_config(self) -> Dict[str, Any]:
        """加载配置

        Returns:
            Dict[str, Any]: 配置字典

        Raises:
            ConfigNotFoundError: 当配置文件不存在时抛出
            ConfigParseError: 当配置文件解析失败时抛出
            ConfigValidationError: 当配置验证失败时抛出
        """
        # 如果配置文件存在，从文件加载配置
        if os.path.exists(self.config_file):
            try:
                # 根据文件扩展名选择解析方法
                if self.config_file.endswith('.toml'):
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = toml.load(f)
                elif self.config_file.endswith('.json'):
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                else:
                    error_msg = f"不支持的配置文件格式: {self.config_file}"
                    if self.logger:
                        self.logger.error(error_msg)
                    raise ConfigParseError(error_msg, {"file": self.config_file})

                # 处理字符串形式的布尔值
                if self.schema:
                    for key, value in config.items():
                        if key in self.schema and self.schema[key].get("type") == "boolean" and isinstance(value, str):
                            if value.lower() == "true":
                                config[key] = True
                            elif value.lower() == "false":
                                config[key] = False

                # 验证配置
                self._validate_config(config)

                # 合并默认配置，确保所有必要的配置项都存在
                merged_config = self.default_config.copy()
                merged_config.update(config)

                if self.logger:
                    self.logger.debug(f"成功加载配置文件: {self.config_file}")

                return merged_config
            except ConfigError:
                # 重新抛出配置错误，以便上层捕获
                raise
            except Exception as e:
                error_msg = f"加载配置文件失败: {self.config_file}, 错误: {e}"
                if self.logger:
                    self.logger.error(error_msg)
                raise ConfigParseError(error_msg, {"file": self.config_file, "error": str(e)}, e)
        else:
            # 如果配置文件不存在，使用默认配置并保存
            if self.logger:
                self.logger.info(f"配置文件不存在，将使用默认配置生成配置文件: {self.config_file}")

            config = self.default_config.copy()
            self.save_config(config)
            return config

    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置

        Args:
            config: 要验证的配置

        Returns:
            bool: 验证是否通过

        Raises:
            ConfigValidationError: 当验证失败时抛出
        """
        if not self.schema:
            return True

        for key, schema_item in self.schema.items():
            # 检查必需项
            if schema_item.get("required", False) and key not in config:
                error_msg = f"缺少必需的配置项: {key}"
                if self.logger:
                    self.logger.error(error_msg)
                raise ConfigValidationError(error_msg, {"key": key})

            # 如果配置项不存在，跳过验证
            if key not in config:
                continue

            # 获取配置值
            value = config[key]

            # 验证类型
            if "type" in schema_item:
                expected_type = schema_item["type"]
                if expected_type == "string":
                    expected_type = str
                elif expected_type == "integer":
                    expected_type = int
                elif expected_type == "number":
                    expected_type = (int, float)
                elif expected_type == "boolean":
                    expected_type = bool
                elif expected_type == "array":
                    expected_type = list
                elif expected_type == "object":
                    expected_type = dict

                if isinstance(expected_type, tuple):
                    ConfigValidator.validate_type(value, list(expected_type), key)
                else:
                    ConfigValidator.validate_type(value, expected_type, key)

            # 验证范围
            if "minimum" in schema_item or "maximum" in schema_item:
                ConfigValidator.validate_range(
                    value,
                    min_value=schema_item.get("minimum"),
                    max_value=schema_item.get("maximum"),
                    key=key
                )

            # 验证枚举
            if "enum" in schema_item:
                ConfigValidator.validate_enum(value, schema_item["enum"], key)

            # 验证字符串
            if schema_item.get("type") == "string":
                ConfigValidator.validate_string(
                    value,
                    min_length=schema_item.get("minLength"),
                    max_length=schema_item.get("maxLength"),
                    pattern=schema_item.get("pattern"),
                    key=key
                )

        return True

    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置

        Args:
            config: 要保存的配置，如果为None则保存当前配置

        Returns:
            bool: 操作是否成功

        Raises:
            ConfigError: 当保存配置失败时抛出
        """
        if config is None:
            config = self.config

        # 验证配置
        try:
            self._validate_config(config)
        except ConfigValidationError as e:
            if self.logger:
                self.logger.error(f"配置验证失败: {e}")
            raise

        try:
            # 确保配置文件目录存在
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            # 根据文件扩展名选择序列化方法
            if self.config_file.endswith('.toml'):
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    toml.dump(config, f)
            elif self.config_file.endswith('.json'):
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            else:
                error_msg = f"不支持的配置文件格式: {self.config_file}"
                if self.logger:
                    self.logger.error(error_msg)
                raise ConfigError(error_msg, {"file": self.config_file})

            # 更新当前配置
            self.config = config

            # 更新文件修改时间
            self.last_modified_time = self._get_file_modified_time()

            if self.logger:
                self.logger.debug(f"成功保存配置文件: {self.config_file}")

            return True
        except ConfigError:
            # 重新抛出配置错误，以便上层捕获
            raise
        except Exception as e:
            error_msg = f"保存配置文件失败: {self.config_file}, 错误: {e}"
            if self.logger:
                self.logger.error(error_msg)
            raise ConfigError(error_msg, {"file": self.config_file, "error": str(e)}, e)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项

        Args:
            key: 配置项键名
            default: 默认值

        Returns:
            配置项值
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any, save: bool = True) -> None:
        """设置配置项

        Args:
            key: 配置项键名
            value: 配置项值
            save: 是否保存配置文件
        """
        # 如果有模式，验证配置项
        if key in self.schema:
            schema_item = self.schema[key]

            # 处理字符串形式的布尔值
            if schema_item.get("type") == "boolean" and isinstance(value, str):
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False

            # 验证类型
            if "type" in schema_item:
                expected_type = schema_item["type"]
                if expected_type == "string":
                    expected_type = str
                elif expected_type == "integer":
                    expected_type = int
                elif expected_type == "number":
                    expected_type = (int, float)
                elif expected_type == "boolean":
                    expected_type = bool
                elif expected_type == "array":
                    expected_type = list
                elif expected_type == "object":
                    expected_type = dict

                if isinstance(expected_type, tuple):
                    ConfigValidator.validate_type(value, list(expected_type), key)
                else:
                    ConfigValidator.validate_type(value, expected_type, key)

            # 验证范围
            if "minimum" in schema_item or "maximum" in schema_item:
                ConfigValidator.validate_range(
                    value,
                    min_value=schema_item.get("minimum"),
                    max_value=schema_item.get("maximum"),
                    key=key
                )

            # 验证枚举
            if "enum" in schema_item:
                ConfigValidator.validate_enum(value, schema_item["enum"], key)

            # 验证字符串
            if schema_item.get("type") == "string":
                ConfigValidator.validate_string(
                    value,
                    min_length=schema_item.get("minLength"),
                    max_length=schema_item.get("maxLength"),
                    pattern=schema_item.get("pattern"),
                    key=key
                )

        # 设置配置项
        self.config[key] = value

        # 保存配置
        if save:
            self.save_config()

    def update(self, config: Dict[str, Any], save: bool = True) -> None:
        """更新配置

        Args:
            config: 要更新的配置
            save: 是否保存配置文件
        """
        # 验证配置
        for key, value in config.items():
            if key in self.schema:
                schema_item = self.schema[key]

                # 处理字符串形式的布尔值
                if schema_item.get("type") == "boolean" and isinstance(value, str):
                    if value.lower() == "true":
                        config[key] = True
                    elif value.lower() == "false":
                        config[key] = False
                    value = config[key]  # 更新value变量

                # 验证类型
                if "type" in schema_item:
                    expected_type = schema_item["type"]
                    if expected_type == "string":
                        expected_type = str
                    elif expected_type == "integer":
                        expected_type = int
                    elif expected_type == "number":
                        expected_type = (int, float)
                    elif expected_type == "boolean":
                        expected_type = bool
                    elif expected_type == "array":
                        expected_type = list
                    elif expected_type == "object":
                        expected_type = dict

                    if isinstance(expected_type, tuple):
                        ConfigValidator.validate_type(value, list(expected_type), key)
                    else:
                        ConfigValidator.validate_type(value, expected_type, key)

                # 验证范围
                if "minimum" in schema_item or "maximum" in schema_item:
                    ConfigValidator.validate_range(
                        value,
                        min_value=schema_item.get("minimum"),
                        max_value=schema_item.get("maximum"),
                        key=key
                    )

                # 验证枚举
                if "enum" in schema_item:
                    ConfigValidator.validate_enum(value, schema_item["enum"], key)

                # 验证字符串
                if schema_item.get("type") == "string":
                    ConfigValidator.validate_string(
                        value,
                        min_length=schema_item.get("minLength"),
                        max_length=schema_item.get("maxLength"),
                        pattern=schema_item.get("pattern"),
                        key=key
                    )

        # 更新配置
        self.config.update(config)

        # 保存配置
        if save:
            self.save_config()

    def reset(self) -> None:
        """重置配置为默认值"""
        self.config = self.default_config.copy()
        self.save_config()

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册配置变更回调函数

        Args:
            callback: 回调函数，接收新的配置作为参数
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """取消注册配置变更回调函数

        Args:
            callback: 回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def _notify_callbacks(self) -> None:
        """通知所有回调函数配置已变更"""
        for callback in self.callbacks:
            try:
                callback(self.config)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"配置变更回调函数执行失败: {e}")

    def start_watching(self, interval: int = 5) -> None:
        """开始监视配置文件变更

        Args:
            interval: 检查间隔（秒）
        """
        if self.is_watching:
            return

        self.watch_interval = interval
        self.is_watching = True

        def watch_thread_func():
            while self.is_watching:
                try:
                    # 获取文件当前修改时间
                    current_time = self._get_file_modified_time()

                    # 如果文件已经被修改，重新加载配置
                    if current_time > self.last_modified_time:
                        if self.logger:
                            self.logger.debug(f"检测到配置文件变更: {self.config_file}")

                        # 重新加载配置
                        try:
                            new_config = self._load_config()

                            # 更新当前配置
                            self.config = new_config

                            # 更新文件修改时间
                            self.last_modified_time = current_time

                            # 通知回调函数
                            self._notify_callbacks()

                            if self.logger:
                                self.logger.info(f"成功热加载配置文件: {self.config_file}")
                        except Exception as e:
                            if self.logger:
                                self.logger.error(f"热加载配置文件失败: {self.config_file}, 错误: {e}")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"监视配置文件失败: {self.config_file}, 错误: {e}")

                # 等待指定时间
                time.sleep(self.watch_interval)

        # 创建并启动监视线程
        self.watch_thread = threading.Thread(target=watch_thread_func, daemon=True)
        self.watch_thread.start()

        if self.logger:
            self.logger.info(f"开始监视配置文件: {self.config_file}, 间隔: {interval}秒")

    def stop_watching(self) -> None:
        """停止监视配置文件变更"""
        if not self.is_watching:
            return

        self.is_watching = False

        # 等待监视线程结束
        if self.watch_thread and self.watch_thread.is_alive():
            self.watch_thread.join(timeout=self.watch_interval + 1)

        if self.logger:
            self.logger.info(f"停止监视配置文件: {self.config_file}")

def get_app_data_folder(app_name: str) -> str:
    """获取应用数据目录

    Args:
        app_name: 应用名称

    Returns:
        str: 应用数据目录路径
    """
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        if not appdata:
            raise EnvironmentError("APPDATA environment variable is not set.")
        path = os.path.join(appdata, app_name)
    elif sys.platform == "darwin":
        home = os.path.expanduser("~")
        path = os.path.join(home, "Library", "Application Support", app_name)
    else:
        home = os.path.expanduser("~")
        path = os.path.join(home, ".local", "share", app_name)

    # 确保目录存在
    if not os.path.exists(path):
        os.makedirs(path)

    return path
