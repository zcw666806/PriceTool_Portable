@echo off
setlocal
set BASE_DIR=%~dp0
set TARGET=%BASE_DIR%PriceTool_Portable

if exist "%TARGET%" rmdir /s /q "%TARGET%"
mkdir "%TARGET%"

xcopy "%BASE_DIR%app" "%TARGET%\app" /E /I /Y
xcopy "%BASE_DIR%src" "%TARGET%\src" /E /I /Y
xcopy "%BASE_DIR%config" "%TARGET%\config" /E /I /Y
xcopy "%BASE_DIR%.streamlit" "%TARGET%\.streamlit" /E /I /Y
mkdir "%TARGET%\data" "%TARGET%\output" "%TARGET%\logs" "%TARGET%\temp"
copy "%BASE_DIR%launcher.py" "%TARGET%\launcher.py"
copy "%BASE_DIR%启动工具.bat" "%TARGET%\启动工具.bat"
copy "%BASE_DIR%关闭工具.bat" "%TARGET%\关闭工具.bat"
copy "%BASE_DIR%重启工具.bat" "%TARGET%\重启工具.bat"
copy "%BASE_DIR%打开页面.bat" "%TARGET%\打开页面.bat"
copy "%BASE_DIR%requirements-portable.txt" "%TARGET%\requirements-portable.txt"
copy "%BASE_DIR%README_使用说明.txt" "%TARGET%\README_使用说明.txt"

echo 已生成便携目录骨架：%TARGET%
echo 请将 Windows embeddable Python 解压到 %TARGET%\python 后安装 requirements-portable.txt
endlocal
