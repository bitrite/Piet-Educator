@echo off
setlocal
set "PIET_EDUCATOR_HOME=%~dp0.."
"%PIET_EDUCATOR_HOME%\runtime\Scripts\python.exe" "%~dp0windows_launcher.py" --home "%PIET_EDUCATOR_HOME%" %*
if errorlevel 1 (
  echo.
  echo Run Install-Windows.cmd again if a requirement is missing.
  pause
  exit /b 1
)
