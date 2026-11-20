@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 launch_app.py %*
  exit /b %errorlevel%
)
where python >nul 2>nul
if %errorlevel%==0 (
  python launch_app.py %*
  exit /b %errorlevel%
)
echo Python 3 was not found on PATH. Install Python 3 from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
pause
