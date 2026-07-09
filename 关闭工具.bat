@echo off
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501"') do taskkill /PID %%a /F
echo 工具已关闭
pause
