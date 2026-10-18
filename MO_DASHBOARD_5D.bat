@echo off
setlocal
set "ATTEND_TARGET=%~dp0BO_DASHBOARD_ORB_5D"
set "ATTEND_UPDATE=%~dp0BO_CAP_NHAT_5D\ChamCong.exe"
if /I "%~1"=="--check-only" (
 if exist "%ATTEND_UPDATE%" exit /b 0
 if exist "%ATTEND_TARGET%\ChamCong.exe" exit /b 0
 exit /b 1
)
if exist "%ATTEND_UPDATE%" (
 if not exist "%ATTEND_TARGET%" (
  mkdir "%ATTEND_TARGET%"
  if errorlevel 1 goto update_failed
 )
 powershell.exe -NoProfile -NonInteractive -Command "$updateHash = (Get-FileHash -LiteralPath $env:ATTEND_UPDATE).Hash; $installedHash = (Get-FileHash -LiteralPath ($env:ATTEND_TARGET + '\ChamCong.exe') -ErrorAction SilentlyContinue).Hash; if ($installedHash -and $updateHash -eq $installedHash) { exit 0 } else { exit 1 }" >nul 2>&1
 if errorlevel 1 (
  copy /y "%ATTEND_UPDATE%" "%ATTEND_TARGET%\ChamCong.exe" >nul
  if errorlevel 1 goto update_failed
 )
)
if not exist "%ATTEND_TARGET%\ChamCong.exe" goto missing
if /I "%~1"=="--apply-only" exit /b 0
start "" "%ATTEND_TARGET%\ChamCong.exe"
exit /b 0
:update_failed
echo Cannot apply the interface update. Close the running ChamCong app and retry.
pause
exit /b 1
:missing
echo Missing executable. Extract the full package or build the project first.
pause
exit /b 1
