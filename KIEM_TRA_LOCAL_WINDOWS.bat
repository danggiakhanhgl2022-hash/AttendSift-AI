@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Missing Python environment. Run CAI_DAT_WINDOWS.bat.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" tools\check_local_install.py
pause
