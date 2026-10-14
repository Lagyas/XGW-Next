@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if errorlevel 1 exit /b 1
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Missing .venv. Run build-local-windows.bat first.
  exit /b 1
)
set "PYTHONPATH=%CD%\editor"
".venv\Scripts\python.exe" -m pytest tests -q
if errorlevel 1 exit /b 1
if not exist "dist\XGW-Next.exe" (
  echo ERROR: Windows EXE missing. Run build-local-windows.bat.
  exit /b 1
)
for %%F in ("dist\XGW-Next.exe") do if %%~zF LEQ 0 exit /b 1
echo Automated preflight passed. MANUAL Windows GUI/MIDI checks are still required.
exit /b 0
