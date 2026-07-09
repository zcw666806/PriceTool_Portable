@echo off
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo.
echo ========================================
echo  UK Order Price Tool
echo ========================================
echo Starting the local tool. Please wait...
echo.
echo Tips:
echo  - If the tool is already running, the browser page will open directly.
echo  - Local page: http://127.0.0.1:8501
echo  - If startup fails, check logs\startup.log
echo.

if exist "%BASE_DIR%python\python.exe" (
  set "PYTHONHOME=%BASE_DIR%python"
  set "PYTHONPATH=%BASE_DIR%;%BASE_DIR%app;%BASE_DIR%python\Lib\site-packages"
  "%BASE_DIR%python\python.exe" "%BASE_DIR%launcher.py"
) else if exist "%BASE_DIR%runtime\python\python.exe" (
  set "PYTHONHOME=%BASE_DIR%runtime\python"
  set "PYTHONPATH=%BASE_DIR%;%BASE_DIR%app;%BASE_DIR%runtime\python\Lib\site-packages"
  "%BASE_DIR%runtime\python\python.exe" "%BASE_DIR%launcher.py"
) else (
  python "%BASE_DIR%launcher.py"
)

echo.
echo Next:
echo  - If the browser did not open, double-click open_page.cmd.
echo  - When finished, double-click stop_tool.cmd.
echo  - After updating files, double-click restart_tool.cmd.
echo.
pause
