@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RecordScreen.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo Program exited with error code %EXIT_CODE%.
  pause
)

exit /b %EXIT_CODE%
