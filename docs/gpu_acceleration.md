# GPU 加速 OCR 处理

本文档介绍如何启用 GPU 加速来提高 OCR 处理速度。

## 系统要求

要使用 GPU 加速 OCR 处理，您需要：

1. NVIDIA GPU（如您的 MX150）
2. 已安装 CUDA 驱动程序（建议 CUDA 11.0 或更高版本）
3. 已安装 cuDNN 库（与 CUDA 版本兼容）

## 安装步骤

### 1. 安装 GPU 版本的 ONNX Runtime

我们提供了一个安装脚本来自动安装所需的依赖项：

```bash
python scripts/install_gpu_support.py
```

这个脚本会：
- 检测您系统上的 NVIDIA GPU
- 检测已安装的 CUDA 版本
- 安装适合您系统的 GPU 版本的 ONNX Runtime
- 安装最新版本的 RapidOCR

### 2. 手动安装（如果自动脚本失败）

如果自动安装脚本失败，您可以手动安装所需的依赖项：

```bash
# 安装 GPU 版本的 ONNX Runtime
pip install onnxruntime-gpu

# 安装 RapidOCR
pip install rapidocr_onnxruntime
```

## 验证 GPU 加速

安装完成后，您可以运行测试脚本来验证 GPU 加速是否正常工作：

```bash
python tests/test_gpu_ocr.py
```

如果一切正常，您应该会看到类似以下的输出：

```
测试 GPU 可用性...
✅ GPU 可用，可以使用 GPU 加速 OCR

测试 OCR 性能 (5 张图像, 3 次运行)...

单张图像 OCR 性能测试:
  运行 1: 0.1234 秒
  运行 2: 0.1123 秒
  运行 3: 0.1145 秒
  平均时间: 0.1167 秒

批量图像 OCR 性能测试:
  运行 1: 0.5678 秒 (平均每张 0.1136 秒)
  运行 2: 0.5432 秒 (平均每张 0.1086 秒)
  运行 3: 0.5543 秒 (平均每张 0.1109 秒)
  总平均时间: 0.5551 秒 (平均每张 0.1110 秒)

使用 GPU 的 OCR 性能总结:
  单张图像平均时间: 0.1167 秒
  批量处理平均时间: 0.5551 秒 (每张 0.1110 秒)
```

## 故障排除

如果您遇到问题，请检查以下几点：

1. **确认 NVIDIA GPU 驱动程序已正确安装**
   
   运行 `nvidia-smi` 命令，应该显示您的 GPU 信息和驱动程序版本。

2. **确认 CUDA 已正确安装**
   
   运行 `nvcc --version` 命令，应该显示 CUDA 编译器版本。

3. **检查 ONNX Runtime 是否支持 GPU**
   
   运行以下 Python 代码：
   
   ```python
   import onnxruntime as ort
   print(ort.get_available_providers())
   ```
   
   输出应该包含 `CUDAExecutionProvider`。

4. **检查日志**
   
   查看应用程序日志文件（`~/.local/share/MemoCoco/memococo.log`），寻找与 GPU 相关的错误消息。

## 性能优化建议

1. **调整批处理大小**
   
   如果您有足够的 GPU 内存，可以增加批处理大小以提高性能。在 `memococo/ocr.py` 文件中修改以下参数：
   
   ```python
   params["Rec.rec_batch_num"] = 12  # 增加到更大的值，如 16 或 24
   params["Cls.cls_batch_num"] = 12  # 增加到更大的值，如 16 或 24
   ```

2. **减少图像预处理**
   
   如果 OCR 准确率不是最重要的，可以减少图像预处理步骤以提高速度。

3. **监控 GPU 内存使用**
   
   使用 `nvidia-smi` 命令监控 GPU 内存使用情况，确保不会耗尽 GPU 内存。

## 已知问题

1. **MX150 显卡内存有限**
   
   MX150 显卡只有 2GB 显存，可能无法处理非常大的图像或大批量的 OCR 任务。如果遇到内存不足的问题，请减小批处理大小或图像尺寸。

2. **首次运行较慢**
   
   首次运行 OCR 时，ONNX Runtime 需要编译和优化模型，可能会比较慢。后续运行会更快。
