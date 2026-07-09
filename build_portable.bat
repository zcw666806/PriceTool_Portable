@echo off
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo.
echo build_portable.bat is kept only for compatibility.
echo The project now uses package_release.cmd.
echo.

call "%BASE_DIR%package_release.cmd"
