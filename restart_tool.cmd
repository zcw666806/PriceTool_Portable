@echo off
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo.
echo ========================================
echo  UK Order Price Tool
echo ========================================
echo Restarting the tool. Please wait...
echo.

call "%BASE_DIR%stop_tool.cmd" /silent
timeout /t 2 /nobreak >nul
call "%BASE_DIR%start_tool.cmd"
