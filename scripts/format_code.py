#!/usr/bin/env python3
"""
代码格式化脚本

用于自动格式化项目中的Python代码，确保符合代码风格规范
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

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

def format_code(check_only=False, path=None):
    """格式化代码

    Args:
        check_only: 是否只检查而不修改代码
        path: 要格式化的路径，默认为整个项目
    
    Returns:
        bool: 是否所有命令都成功执行
    """
    target_path = path or PROJECT_ROOT
    success = True

    # 运行isort
    isort_command = ["isort"]
    if check_only:
        isort_command.append("--check")
    isort_command.append(str(target_path))
    success = run_command(isort_command, "排序导入语句") and success

    # 运行black
    black_command = ["black"]
    if check_only:
        black_command.append("--check")
    black_command.append(str(target_path))
    success = run_command(black_command, "格式化代码") and success

    # 运行flake8
    flake8_command = ["flake8", str(target_path)]
    success = run_command(flake8_command, "检查代码风格") and success

    # 运行mypy（可选）
    mypy_command = ["mypy", str(target_path)]
    success = run_command(mypy_command, "类型检查") and success

    return success

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="格式化Python代码")
    parser.add_argument("--check", action="store_true", help="只检查代码，不修改")
    parser.add_argument("--path", help="要格式化的路径，默认为整个项目")
    args = parser.parse_args()

    # 切换到项目根目录
    os.chdir(PROJECT_ROOT)

    # 格式化代码
    success = format_code(check_only=args.check, path=args.path)

    # 返回状态码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
