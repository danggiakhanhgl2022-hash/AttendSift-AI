@echo off
setlocal
cd /d "%~dp0"
echo ==================================================
echo ChamCongChatwork - SETUP LOCAL (Windows)
echo ==================================================
set "PYTHON_CMD="
py -3.11 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3.11"
if not defined PYTHON_CMD (
  py -3.12 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
  if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)
if not defined PYTHON_CMD (
  python -c "import sys; assert sys.version_info >= (3,11) and sys.version_info < (3,14)" >nul 2>&1
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo ERROR: Install Python 3.11 x64 from python.org, enable Python Launcher.
  echo See README.md for details.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating isolated environment...
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto failure
)
echo Installing local packages (Internet needed the first time)...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-local.txt
if errorlevel 1 goto failure
".venv\Scripts\python.exe" tools\check_local_install.py
if errorlevel 1 goto failure
echo.
echo SUCCESS. Now double-click CHAY_LOCAL_WINDOWS.bat.
pause
exit /b 0
:failure
echo FAILED. Check network, Python and folder permissions.
pause
exit /b 1
