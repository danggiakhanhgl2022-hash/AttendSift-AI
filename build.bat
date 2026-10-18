@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --distpath BO_CAP_NHAT_5D --workpath build-panels ChamCong.spec
if errorlevel 1 exit /b 1
if exist HUONG_DAN_SU_DUNG.pdf copy /y HUONG_DAN_SU_DUNG.pdf BO_CAP_NHAT_5D\HUONG_DAN_SU_DUNG.pdf >nul
echo Build complete: BO_CAP_NHAT_5D\ChamCong.exe
