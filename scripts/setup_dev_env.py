#!/usr/bin/env python3
"""
开发环境设置脚本

用于安装开发环境所需的工具和配置
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 开发依赖
DEV_DEPENDENCIES = [
    "black",
    "flake8",
    "flake8-docstrings",
    "isort",
    "mypy",
    "pre-commit",
    "pytest",
    "pytest-cov",
    "types-requests",
    "types-toml",
]

def run_command(command, description):
    """运行命令并打印结果

    Args:
        command: 要运行的命令
        description: 命令的描述
    
    Returns:
        bool: 命令是否成功执行
    """
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description}成功")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description}失败")
        print(e.stderr)
        return False

def install_dev_dependencies():
    """安装开发依赖"""
    command = [sys.executable, "-m", "pip", "install"] + DEV_DEPENDENCIES
    return run_command(command, "安装开发依赖")

def setup_pre_commit():
    """设置pre-commit钩子"""
    command = ["pre-commit", "install"]
    return run_command(command, "设置pre-commit钩子")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="设置开发环境")
    parser.add_argument("--skip-deps", action="store_true", help="跳过安装开发依赖")
    parser.add_argument("--skip-hooks", action="store_true", help="跳过设置pre-commit钩子")
    args = parser.parse_args()

    # 切换到项目根目录
    os.chdir(PROJECT_ROOT)

    success = True

    # 安装开发依赖
    if not args.skip_deps:
        success = install_dev_dependencies() and success

    # 设置pre-commit钩子
    if not args.skip_hooks:
        success = setup_pre_commit() and success

    # 返回状态码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
