@echo off
set BASE_DIR=%~dp0
cd /d "%BASE_DIR%"

if exist "%BASE_DIR%python\python.exe" (
  set PYTHONHOME=%BASE_DIR%python
  set PYTHONPATH=%BASE_DIR%;%BASE_DIR%app;%BASE_DIR%python\Lib\site-packages
  "%BASE_DIR%python\python.exe" "%BASE_DIR%launcher.py"
) else (
  python "%BASE_DIR%launcher.py"
)

pause
