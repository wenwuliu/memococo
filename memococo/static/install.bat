@echo off
:: 设置脚本标题
title 安装并设置 memococo 开机自启动

:: 强制使用 UTF-8 编码
chcp 65001 >nul

:: 打印提示信息
echo 正在安装 memococo 程序...

:: 下载到本地
python -m pip install --no-cache-dir git+https://github.com/wenwuliu/memococo.git
if %errorlevel% neq 0 (
    echo 安装失败，请检查网络或 pip 配置。
    pause
    exit /b 1
)

:: 获取当前用户的启动文件夹路径
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

:: 创建快捷方式名称和路径
set "SHORTCUT_NAME=memococo.lnk"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\%SHORTCUT_NAME%"

:: 检查是否已存在同名快捷方式
if exist "%SHORTCUT_PATH%" (
    echo 快捷方式已存在，跳过创建。
) else (
    echo 正在创建开机自启动快捷方式...
    
    :: 使用 PowerShell 创建快捷方式（修复变量引用和路径问题）
    powershell -Command " ^
        $ws = New-Object -ComObject WScript.Shell; ^
        $sc = $ws.CreateShortcut([System.Environment]::ExpandEnvironmentVariables('%SHORTCUT_PATH%')); ^
        $sc.TargetPath = 'python'; ^
        $sc.Arguments = '-m memococo.app'; ^
        $sc.WorkingDirectory = [System.Environment]::ExpandEnvironmentVariables('%%USERPROFILE%%'); ^
        $sc.Save(); ^
        if ($?) { Write-Host '快捷方式创建成功' } else { Write-Host '快捷方式创建失败' }"
    
    if %errorlevel% neq 0 (
        echo 创建快捷方式失败，请手动设置开机自启动。
        pause
        exit /b 1
    )
)

:: 验证安装
echo 正在验证安装...
python -c "import memococo; print('memococo 版本:', memococo.__version__)"
if %errorlevel% neq 0 (
    echo 验证失败，请检查安装是否正确。
    pause
    exit /b 1
)

:: 完成提示
echo.
echo =====================================================
echo memococo 已成功安装并设置为开机自启动！
echo 启动路径："%SHORTCUT_PATH%"
echo =====================================================
pause
exit /b 0