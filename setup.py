import platform
from pathlib import Path
from setuptools import find_packages, setup

# 读取README.md文件
readme_path = Path("README.md")
long_description = readme_path.read_text(encoding="utf-8")

# 基础依赖包
install_requires = [
    "Flask>=3.0.3", 
    "numpy>=1.26.4",
    "mss>=9.0.1", 
    "toml>=0.10.2",
    "pyautogui>=0.9.54",
    "ffmpeg-python>=0.2.0",
    "rapidocr_onnxruntime>=1.2.3",
    "requests>=2.32.3",
    "jsonify>=0.5",
]

# 操作系统特定依赖
OS_DEPENDENCIES = {
    "windows": ["pywin32", "psutil"],
    "darwin": ["pyobjc>=10.3"],
    "linux": []
}

# 获取当前操作系统并添加对应依赖
current_os = platform.system().lower()
if current_os in OS_DEPENDENCIES:
    install_requires.extend(OS_DEPENDENCIES[current_os])

setup(
    name="MemoCoco",
    version="2.1.47",
    description="MemoCoco - 时间胶囊",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="liuwenwu",
    author_email="liuawu625@163.com",
    packages=find_packages(),
    python_requires=">=3.8",  # 指定Python最低版本要求
    install_requires=install_requires,
    # entry_points={
    #     "console_scripts":[
    #         'memococo=memococo.app:main',
    #     ],
    # },
    # data_files=[
    #     ('/usr/share/memococo', ['debian/memococo.service']),
    # ],
    # options={
    #     'install': {'install_lib': "/usr/lib/python3/dist-packages"},
    #     'bdist_deb': {'install_root': "~/.local"},
    # },
    include_package_data=True,
    extras_require=OS_DEPENDENCIES,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
