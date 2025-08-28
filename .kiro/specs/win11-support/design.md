# Design Document

## Overview

本设计文档详细说明了如何将MemoCoco应用程序从支持Windows 10升级为专门支持Windows 11的实现方案。我们将重点关注Windows 11特有的API和功能，同时放弃对Windows 10的兼容性支持，以简化代码并提高在Windows 11上的性能和用户体验。

## 架构

MemoCoco在Windows平台上的架构将进行以下调整：

1. **操作系统检测层**：
   - 添加专门的Windows 11版本检测机制
   - 在应用启动时验证操作系统版本，非Windows 11显示不兼容消息

2. **窗口管理层**：
   - 使用Windows 11优化的Win32 API或WinRT API获取窗口信息
   - 考虑Windows 11的窗口管理特性（如Snap Layouts）

3. **截图系统**：
   - 更新截图机制以适应Windows 11的DPI缩放和多显示器设置
   - 优化对Windows 11特有UI元素的捕获

4. **权限管理**：
   - 实现符合Windows 11安全模型的权限请求流程
   - 添加必要的应用程序清单以声明所需权限

5. **数据存储**：
   - 确保使用Windows 11推荐的数据存储位置和API
   - 优化文件系统操作以适应Windows 11的特性

## 组件和接口

### 1. 操作系统检测组件

```python
class WindowsVersionDetector:
    @staticmethod
    def is_windows_11():
        """检测当前操作系统是否为Windows 11"""
        # 实现Windows 11检测逻辑
        pass
    
    @staticmethod
    def show_compatibility_error():
        """显示操作系统不兼容错误"""
        # 实现错误显示逻辑
        pass
```

### 2. 窗口管理组件

```python
class Win11WindowManager:
    @staticmethod
    def get_active_window():
        """获取当前活动窗口信息"""
        # 使用Windows 11优化的API
        pass
    
    @staticmethod
    def get_window_title(hwnd):
        """获取窗口标题"""
        # 实现获取窗口标题的逻辑
        pass
    
    @staticmethod
    def get_window_app_name(hwnd):
        """获取窗口应用程序名称"""
        # 实现获取应用名称的逻辑
        pass
```

### 3. 截图组件

```python
class Win11ScreenshotManager:
    @staticmethod
    def capture_screen():
        """捕获整个屏幕"""
        # 实现屏幕捕获逻辑
        pass
    
    @staticmethod
    def capture_active_window():
        """捕获当前活动窗口"""
        # 实现窗口捕获逻辑
        pass
    
    @staticmethod
    def handle_dpi_scaling(image):
        """处理DPI缩放"""
        # 实现DPI缩放处理逻辑
        pass
```

### 4. 权限管理组件

```python
class Win11PermissionManager:
    @staticmethod
    def request_screenshot_permission():
        """请求截图权限"""
        # 实现权限请求逻辑
        pass
    
    @staticmethod
    def check_admin_privileges():
        """检查管理员权限"""
        # 实现权限检查逻辑
        pass
```

### 5. 数据存储组件

```python
class Win11DataStorage:
    @staticmethod
    def get_app_data_path():
        """获取应用数据存储路径"""
        # 实现路径获取逻辑
        pass
    
    @staticmethod
    def ensure_directory_permissions(path):
        """确保目录权限正确"""
        # 实现权限检查和设置逻辑
        pass
```

## 数据模型

现有的数据模型不需要重大更改，但需要确保与Windows 11的文件系统和数据存储机制兼容。

## 错误处理

1. **操作系统兼容性错误**：
   - 在应用启动时检测操作系统版本
   - 对于非Windows 11系统，显示明确的错误消息并退出

2. **权限错误**：
   - 捕获并处理Windows 11特有的权限拒绝异常
   - 提供清晰的错误消息和解决步骤

3. **窗口管理错误**：
   - 处理无法获取窗口信息的情况
   - 实现优雅的降级策略，确保应用不会崩溃

4. **截图错误**：
   - 处理截图失败的情况
   - 记录详细的错误信息以便调试

## 测试策略

1. **单元测试**：
   - 为每个新组件编写单元测试
   - 模拟Windows 11 API响应

2. **集成测试**：
   - 测试组件之间的交互
   - 验证数据流和错误处理

3. **系统测试**：
   - 在实际的Windows 11环境中测试
   - 测试不同的硬件配置和DPI设置

4. **兼容性测试**：
   - 测试在Windows 11不同版本上的兼容性
   - 验证在非Windows 11系统上的错误处理

## 实现注意事项

1. **API选择**：
   - 优先使用Windows 11引入或优化的API
   - 考虑使用WinRT API代替传统Win32 API，以获得更好的Windows 11集成

2. **DPI感知**：
   - 确保应用正确声明DPI感知能力
   - 实现适当的DPI缩放处理

3. **安全考虑**：
   - 遵循Windows 11的安全最佳实践
   - 实现最小权限原则

4. **性能优化**：
   - 利用Windows 11的性能改进
   - 优化截图和OCR处理流程

5. **用户体验**：
   - 考虑Windows 11的设计语言
   - 确保应用外观与Windows 11一致

## 技术债务

1. 移除所有Windows 10特定的代码和兼容性检查
2. 更新所有依赖库到支持Windows 11的最新版本
3. 重构截图和窗口管理代码以使用最新API

## 依赖关系

1. **pywin32**：更新到最新版本以支持Windows 11 API
2. **pygetwindow**：可能需要替换为更适合Windows 11的库
3. **PIL/Pillow**：确保使用支持Windows 11的最新版本
4. **psutil**：更新到支持Windows 11的版本

## 迁移计划

1. 首先实现操作系统版本检测
2. 更新窗口管理和截图组件
3. 实现权限管理改进
4. 更新数据存储逻辑
5. 移除Windows 10兼容性代码
6. 全面测试Windows 11支持