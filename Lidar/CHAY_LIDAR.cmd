@echo off
chcp 65001 >nul
cd /d "%~dp0chuong_trinh"
set "PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo Chua co moi truong Python. Hay chay CAI_DAT.ps1 tai thu muc goc kho ma.
  pause
  exit /b 1
)
set "LIDAR_PORT=%~1"
if not defined LIDAR_PORT set "LIDAR_PORT=COM9"
"%PYTHON%" -X utf8 lidar_test.py --port "%LIDAR_PORT%" --range 70 --duty 40
pause
