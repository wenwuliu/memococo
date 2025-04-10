# MemoCoco 测试

本目录包含 MemoCoco 应用的所有测试文件。

## 运行测试

### 运行所有测试

```bash
python tests/run_tests.py
```

### 运行特定测试

```bash
python tests/run_tests.py <test_name>
```

例如：

```bash
python tests/run_tests.py ocr_processor
```

或者直接运行特定的测试文件：

```bash
python tests/test_ocr_processor.py
```

## 测试文件说明

- `test_async_compression.py`: 测试异步图像压缩功能
- `test_async_ocr.py`: 测试异步OCR功能
- `test_async_simple.py`: 简单的异步处理测试
- `test_async_tasks.py`: 测试异步任务处理
- `test_config.py`: 测试配置模块
- `test_nlp.py`: 测试自然语言处理功能
- `test_ocr_processor.py`: 测试OCR处理模块
- `test_screenshot_ocr_separation.py`: 测试截图和OCR分离功能
- `test_thread_pool.py`: 测试线程池功能

## 添加新测试

添加新测试时，请遵循以下规则：

1. 测试文件名应以 `test_` 开头
2. 测试类应继承 `unittest.TestCase`
3. 测试方法应以 `test_` 开头
4. 每个测试文件应包含详细的文档字符串，说明测试的目的和功能
5. 所有测试文件都应放在 `tests` 目录中
