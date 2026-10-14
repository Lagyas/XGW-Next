@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "editor\app.py"
) else (
  py -3.12 "editor\app.py"
)
if errorlevel 1 (
  echo ERROR: XGW Next exited with an error.
  pause
  exit /b 1
)
