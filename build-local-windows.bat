@echo off
setlocal
cd /d "%~dp0"
rem Make editor modules available to unittest and application imports.
set "PYTHONPATH=%~dp0editor"
py -3.12 -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip pyinstaller "mido>=1.3,<2" "python-rtmidi>=1.5,<2"
if errorlevel 1 exit /b 1
python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
python -m PyInstaller --noconfirm --clean --onefile --windowed --name XGW-Next --paths editor --collect-submodules mido.backends --hidden-import mido.backends.rtmidi --collect-submodules rtmidi editor/app.py
if errorlevel 1 exit /b 1
if not exist "dist\XGW-Next.exe" (
    echo ERROR: Build finished without dist\XGW-Next.exe
    exit /b 1
)
echo Application: %CD%\dist\XGW-Next.exe
pause
