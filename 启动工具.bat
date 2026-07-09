@echo off
chcp 65001 >nul
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo.
echo ========================================
echo  UK Order 价格查询工具
echo ========================================
echo 正在启动，请稍候...
echo.
echo 提示：
echo  - 如果工具已经在运行，会直接打开浏览器页面。
echo  - 页面地址固定为 http://127.0.0.1:8501
echo  - 启动失败时，请查看 logs\startup.log
echo.

if exist "%BASE_DIR%python\python.exe" (
  set "PYTHONHOME=%BASE_DIR%python"
  set "PYTHONPATH=%BASE_DIR%;%BASE_DIR%app;%BASE_DIR%python\Lib\site-packages"
  "%BASE_DIR%python\python.exe" "%BASE_DIR%launcher.py"
) else (
  python "%BASE_DIR%launcher.py"
)

echo.
echo 操作提示：
echo  - 如果浏览器没有自动打开，请双击“打开页面.bat”。
echo  - 使用完成后，请双击“关闭工具.bat”。
echo  - 更新工具文件后，请双击“重启工具.bat”。
echo.
pause
