@echo off
setlocal
echo Piet Educator - Windows Setup
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows\Install-PietEducator.ps1"
if errorlevel 1 (
  echo.
  echo Setup did not finish. Read the message above, then run this file again.
  pause
  exit /b 1
)
echo.
echo Setup finished. Use the Piet Educator shortcut on your Desktop.
pause
