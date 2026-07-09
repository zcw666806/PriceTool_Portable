@echo off
chcp 65001 >nul
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo.
echo ========================================
echo  UK Order 价格查询工具
echo ========================================
echo 正在打开工具页面...
echo 如果提示工具没有运行，请先双击“启动工具.bat”。
echo.

if exist "%BASE_DIR%python\python.exe" (
  set "PYTHONHOME=%BASE_DIR%python"
  set "PYTHONPATH=%BASE_DIR%;%BASE_DIR%app;%BASE_DIR%python\Lib\site-packages"
  "%BASE_DIR%python\python.exe" "%BASE_DIR%launcher.py" --open
) else (
  python "%BASE_DIR%launcher.py" --open
)

echo.
pause
