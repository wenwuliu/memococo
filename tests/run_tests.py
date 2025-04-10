#!/usr/bin/env python3
"""
MemoCoco测试运行脚本

用于运行所有测试或指定的测试模块
"""

import os
import sys
import unittest
import argparse

def run_all_tests():
    """运行所有测试"""
    # 获取tests目录
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 将项目根目录添加到Python路径
    project_root = os.path.dirname(tests_dir)
    sys.path.insert(0, project_root)
    
    # 发现并运行所有测试
    test_suite = unittest.defaultTestLoader.discover(tests_dir, pattern="test_*.py")
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(test_suite)

def run_specific_test(test_name):
    """运行指定的测试模块"""
    # 获取tests目录
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 将项目根目录添加到Python路径
    project_root = os.path.dirname(tests_dir)
    sys.path.insert(0, project_root)
    
    # 导入并运行指定的测试模块
    if not test_name.startswith('test_'):
        test_name = f'test_{test_name}'
    if not test_name.endswith('.py'):
        test_name = f'{test_name}.py'
    
    test_path = os.path.join(tests_dir, test_name)
    if not os.path.exists(test_path):
        print(f"Error: Test file '{test_name}' not found in {tests_dir}")
        sys.exit(1)
    
    # 将测试文件名转换为模块名
    module_name = f'tests.{test_name[:-3]}'
    
    # 导入模块
    try:
        __import__(module_name)
        module = sys.modules[module_name]
        
        # 如果模块有main函数，直接调用
        if hasattr(module, 'main'):
            module.main()
        # 否则，尝试运行所有测试用例
        else:
            test_suite = unittest.defaultTestLoader.loadTestsFromModule(module)
            test_runner = unittest.TextTestRunner(verbosity=2)
            test_runner.run(test_suite)
    except ImportError as e:
        print(f"Error importing test module: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MemoCoco tests")
    parser.add_argument('test', nargs='?', help='Specific test to run (without test_ prefix)')
    args = parser.parse_args()
    
    if args.test:
        run_specific_test(args.test)
    else:
        run_all_tests()
