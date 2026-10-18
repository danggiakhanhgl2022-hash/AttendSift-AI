@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run CAI_DAT_WINDOWS.bat first.
  pause
  exit /b 1
)
echo Installing desktop and build dependencies...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 goto failure
echo Building portable Windows EXE...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --distpath release --workpath build ChamCong.spec
if errorlevel 1 goto failure
if not exist "release\ChamCong.exe" goto failure
echo.
echo SUCCESS: release\ChamCong.exe
if exist "HUONG_DAN_SU_DUNG.pdf" copy /y "HUONG_DAN_SU_DUNG.pdf" "release\HUONG_DAN_SU_DUNG.pdf" >nul
echo Copy ChamCong.exe to a writable folder on another Windows PC.
echo Keys must be entered again on another machine.
pause
exit /b 0
:failure
echo Build failed. Check error messages above.
pause
exit /b 1
