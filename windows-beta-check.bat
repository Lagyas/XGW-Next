@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\editor"
where py >nul 2>nul
if errorlevel 1 (echo Python launcher not found & exit /b 1)
py -3 -c "import tkinter; import sys; print('Python:',sys.version); print('Tk:',tkinter.TkVersion)"
if errorlevel 1 exit /b 1
py -3 -m unittest discover -s tests -q
if errorlevel 1 exit /b 1
py -3 -c "import sys; sys.path.insert(0,'editor'); import app, piano_roll, drum_editor, xg_part_editor; print('GUI module imports OK')"
if errorlevel 1 exit /b 1
echo Automated checks passed. Manually test MIDI ports, playback, recording, mixer, and XG SysEx.
exit /b 0
