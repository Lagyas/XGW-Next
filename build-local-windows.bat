@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if errorlevel 1 exit /b 1
set "PYTHONPATH=%CD%\editor"
where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python launcher 'py' not found. Install Python 3.12.
  exit /b 1
)
py -3.12 -m venv .venv
if errorlevel 1 exit /b 1
call ".venv\Scripts\activate.bat"
if errorlevel 1 exit /b 1
python -m pip install --upgrade pip pyinstaller "mido>=1.3,<2" "python-rtmidi>=1.5,<2" "pytest>=8,<10"
if errorlevel 1 exit /b 1
python -m pytest tests -q
if errorlevel 1 (
  echo ERROR: Unit tests failed. EXE was not built.
  exit /b 1
)
python tools\write_build_info.py
if errorlevel 1 exit /b 1
python -m PyInstaller --noconfirm --clean XGW-Next.spec
if errorlevel 1 exit /b 1
if not exist "dist\XGW-Next.exe" (
  echo ERROR: Missing dist\XGW-Next.exe
  exit /b 1
)
for %%F in ("dist\XGW-Next.exe") do if %%~zF LEQ 0 (
  echo ERROR: EXE is empty
  exit /b 1
)
echo.
echo SUCCESS: %CD%\dist\XGW-Next.exe
exit /b 0
