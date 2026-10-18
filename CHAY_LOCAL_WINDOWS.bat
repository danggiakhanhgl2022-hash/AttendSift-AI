@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Not installed. Run CAI_DAT_WINDOWS.bat first.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -u tools\run_local.py
if errorlevel 1 (
  echo App stopped with an error. Look at logs\application.log.
  pause
)
