# MemoCoco 代码风格指南

本文档定义了 MemoCoco 项目的代码风格规范，旨在保持代码的一致性和可读性。所有贡献者都应遵循这些规范。

## 1. 命名约定

### 1.1 Python 代码

- **模块名**：使用全小写字母，如果需要多个单词，使用下划线分隔（snake_case）
  - 正确：`database.py`, `error_handler.py`
  - 错误：`Database.py`, `errorHandler.py`

- **类名**：使用 CamelCase（首字母大写的驼峰命名法）
  - 正确：`DatabaseManager`, `ErrorHandler`
  - 错误：`database_manager`, `error_handler`

- **函数名和方法名**：使用 snake_case（全小写，下划线分隔）
  - 正确：`get_timestamps()`, `insert_entry()`
  - 错误：`getTimestamps()`, `insertEntry()`

- **变量名**：使用 snake_case
  - 正确：`user_name`, `timestamp_list`
  - 错误：`userName`, `TimestampList`

- **常量名**：使用全大写字母，单词之间用下划线分隔
  - 正确：`MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`
  - 错误：`maxRetryCount`, `default_timeout`

- **私有属性和方法**：使用单下划线前缀
  - 正确：`_private_method()`, `_internal_variable`
  - 错误：`privateMethod()`, `internalVariable`

### 1.2 HTML/CSS/JavaScript 代码

- **HTML ID**：使用小写字母和连字符（kebab-case）
  - 正确：`user-profile`, `search-box`
  - 错误：`userProfile`, `search_box`

- **CSS 类名**：使用小写字母和连字符（kebab-case）
  - 正确：`nav-item`, `btn-primary`
  - 错误：`navItem`, `btn_primary`

- **JavaScript 变量和函数**：使用 camelCase（首字母小写的驼峰命名法）
  - 正确：`getUserData()`, `pageTitle`
  - 错误：`get_user_data()`, `page_title`

- **JavaScript 类**：使用 PascalCase（首字母大写的驼峰命名法）
  - 正确：`UserProfile`, `SearchEngine`
  - 错误：`userProfile`, `search_engine`

## 2. 缩进和格式化

### 2.1 Python 代码

- 使用 4 个空格进行缩进，不使用制表符（Tab）
- 每行代码最大长度为 100 个字符
- 函数和类定义之间空两行
- 类中的方法之间空一行
- 相关的代码块之间空一行
- 导入语句应按以下顺序排列：
  1. 标准库导入
  2. 相关第三方库导入
  3. 本地应用/库特定导入
- 每组导入之间应该有一个空行

### 2.2 HTML/CSS/JavaScript 代码

- HTML 和 CSS 使用 2 个空格进行缩进
- JavaScript 使用 2 个空格进行缩进
- 每行代码最大长度为 100 个字符
- CSS 属性应按字母顺序排列
- JavaScript 函数之间空一行

## 3. 注释和文档字符串

### 3.1 Python 代码

- 所有模块、类和函数都应该有文档字符串
- 使用 Google 风格的文档字符串格式：

```python
def function_name(param1, param2):
    """函数的简短描述。

    函数的详细描述，可以跨多行。

    Args:
        param1: 第一个参数的描述。
        param2: 第二个参数的描述。

    Returns:
        返回值的描述。

    Raises:
        ValueError: 异常的描述。
    """
    # 函数实现
```

- 行内注释应该与代码分开，并使用完整的句子：

```python
# 这是一个行内注释的例子
x = x + 1  # 增加计数器
```

### 3.2 HTML/CSS/JavaScript 代码

- HTML 文件应该在顶部有注释，说明页面的用途
- CSS 文件应该有注释，说明主要的样式部分
- JavaScript 函数应该有注释，说明函数的用途、参数和返回值

## 4. 代码组织

### 4.1 Python 代码

- 每个模块应该有一个明确的职责
- 相关的功能应该放在同一个模块中
- 使用类来组织相关的函数和数据
- 避免过长的函数，一个函数应该只做一件事
- 避免过深的嵌套，考虑提取子函数

### 4.2 HTML/CSS/JavaScript 代码

- HTML、CSS 和 JavaScript 代码应该分离到不同的文件中
- 使用模板继承来避免重复的 HTML 代码
- CSS 应该使用类选择器，避免使用 ID 选择器
- JavaScript 代码应该模块化，避免全局变量和函数

## 5. 错误处理

- 使用异常而不是返回错误代码
- 捕获具体的异常，而不是捕获所有异常
- 提供有意义的错误消息
- 记录异常信息，包括堆栈跟踪

## 6. 测试

- 为所有功能编写单元测试
- 测试文件应该放在 `tests` 目录中
- 测试文件名应该以 `test_` 开头
- 测试函数名应该以 `test_` 开头
- 测试应该是独立的，不依赖于其他测试的结果

## 7. 版本控制

- 提交消息应该清晰地描述更改内容
- 每个提交应该只包含一个逻辑更改
- 避免提交未完成的代码
- 在合并之前，确保代码通过所有测试

## 8. 工具和自动化

- 使用 `flake8` 进行代码风格检查
- 使用 `black` 进行代码格式化
- 使用 `isort` 对导入语句进行排序
- 使用 `mypy` 进行类型检查

## 9. 示例

### 9.1 Python 模块示例

```python
"""
模块描述

详细描述模块的功能和用途
"""

import os
import sys
from typing import Dict, List, Optional

import numpy as np
import requests

from memococo.common.error_handler import ErrorHandler
from memococo.database import DatabaseManager


class ExampleClass:
    """示例类的描述。

    详细描述类的功能和用途。
    """

    def __init__(self, param1: str, param2: Optional[int] = None):
        """初始化示例类。

        Args:
            param1: 第一个参数的描述。
            param2: 第二个参数的描述，默认为 None。
        """
        self.param1 = param1
        self.param2 = param2
        self._private_var = 0

    def public_method(self, input_data: List[str]) -> Dict[str, Any]:
        """公共方法的描述。

        详细描述方法的功能和用途。

        Args:
            input_data: 输入数据的描述。

        Returns:
            返回值的描述。

        Raises:
            ValueError: 如果输入数据为空。
        """
        if not input_data:
            raise ValueError("Input data cannot be empty")

        # 处理数据
        result = self._private_method(input_data)

        return result

    def _private_method(self, data: List[str]) -> Dict[str, Any]:
        """私有方法的描述。

        Args:
            data: 数据的描述。

        Returns:
            处理后的数据。
        """
        # 实现细节
        return {"result": data}


def main():
    """主函数。"""
    example = ExampleClass("test")
    result = example.public_method(["a", "b", "c"])
    print(result)


if __name__ == "__main__":
    main()
```

### 9.2 HTML/CSS/JavaScript 示例

HTML:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>示例页面</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="page-header">
    <h1 class="page-title">示例页面</h1>
    <nav class="main-nav">
      <ul class="nav-list">
        <li class="nav-item"><a href="#" class="nav-link">首页</a></li>
        <li class="nav-item"><a href="#" class="nav-link">关于</a></li>
      </ul>
    </nav>
  </header>

  <main class="main-content">
    <section class="content-section">
      <h2 class="section-title">内容标题</h2>
      <p class="section-text">内容描述</p>
    </section>
  </main>

  <footer class="page-footer">
    <p class="copyright">版权信息</p>
  </footer>

  <script src="script.js"></script>
</body>
</html>
```

CSS:
```css
/* 页面样式 */
.page-header {
  background-color: #f5f5f5;
  padding: 20px;
}

.page-title {
  color: #333;
  font-size: 24px;
  margin: 0;
}

.main-nav {
  margin-top: 10px;
}

.nav-list {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
}

.nav-item {
  margin-right: 10px;
}

.nav-link {
  color: #007bff;
  text-decoration: none;
}

.main-content {
  padding: 20px;
}

.content-section {
  margin-bottom: 20px;
}

.section-title {
  color: #333;
  font-size: 20px;
}

.section-text {
  color: #666;
  line-height: 1.5;
}

.page-footer {
  background-color: #f5f5f5;
  padding: 20px;
  text-align: center;
}

.copyright {
  color: #666;
  margin: 0;
}
```

JavaScript:
```javascript
/**
 * 示例脚本
 * 
 * 详细描述脚本的功能和用途
 */

// 等待 DOM 加载完成
document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
});

/**
 * 初始化应用
 */
function initializeApp() {
  setupNavigation();
  loadContent();
}

/**
 * 设置导航事件处理
 */
function setupNavigation() {
  const navLinks = document.querySelectorAll('.nav-link');
  
  navLinks.forEach(link => {
    link.addEventListener('click', handleNavClick);
  });
}

/**
 * 处理导航点击事件
 * 
 * @param {Event} event - 点击事件对象
 */
function handleNavClick(event) {
  event.preventDefault();
  
  const target = event.currentTarget;
  console.log(`Clicked on: ${target.textContent}`);
  
  // 导航逻辑
}

/**
 * 加载内容
 */
function loadContent() {
  console.log('Loading content...');
  
  // 内容加载逻辑
}
```
