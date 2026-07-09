@echo off
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

if /I "%~1"=="/silent" goto CLOSE

echo.
echo ========================================
echo  UK Order Price Tool
echo ========================================
echo Stopping the local tool. Please wait...
echo.

:CLOSE
set "PID_FILE=%BASE_DIR%logs\price_tool.pid"
set "CLOSED=0"

if exist "%PID_FILE%" (
  set /p TOOL_PID=<"%PID_FILE%"
  if defined TOOL_PID (
    tasklist /FI "PID eq %TOOL_PID%" 2>nul | find "%TOOL_PID%" >nul
    if not errorlevel 1 (
      taskkill /PID %TOOL_PID% /T /F >nul 2>nul
      set "CLOSED=1"
    )
  )
  del "%PID_FILE%" >nul 2>nul
)

if "%CLOSED%"=="0" (
  for /f "usebackq tokens=2 delims==" %%p in (`wmic process where "CommandLine like '%%streamlit%%streamlit_app.py%%' and CommandLine like '%%%BASE_DIR:\=\\%%%'" get ProcessId /value 2^>nul ^| find "="`) do (
    taskkill /PID %%p /T /F >nul 2>nul
    set "CLOSED=1"
  )
)

if /I "%~1"=="/silent" exit /b 0

if "%CLOSED%"=="1" (
  echo Tool stopped. You can close this window.
) else (
  echo No running tool process was found.
)
echo.
pause
