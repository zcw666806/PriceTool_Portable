@echo off
chcp 65001 >nul
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo.
echo ========================================
echo  UK Order 价格查询工具
echo ========================================
echo 正在重启工具，请稍候...
echo 这会先关闭后台服务，然后重新打开页面。
echo.

call "%BASE_DIR%关闭工具.bat" /silent
timeout /t 2 /nobreak >nul
call "%BASE_DIR%启动工具.bat"
