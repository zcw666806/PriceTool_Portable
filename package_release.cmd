@echo off
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo.
echo ========================================
echo  UK Order Price Tool - Package Release
echo ========================================
echo This will build a clean portable zip from:
echo  - current source files
echo  - runtime\python
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%BASE_DIR%package_release.ps1"

echo.
pause
