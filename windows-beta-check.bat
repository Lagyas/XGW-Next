@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\editor"

rem Use the same Python version as build-local-windows.bat.
where py >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python launcher py.exe not found. Install Python 3.12 for Windows.
    exit /b 1
)
py -3.12 -c "import sys, tkinter; print('Python:',sys.version); print('Tk:',tkinter.TkVersion)"
if errorlevel 1 (
    echo ERROR: Python 3.12 or Tkinter is missing.
    exit /b 1
)

rem Tests use the standard library; GUI MIDI backend requires optional packages.
py -3.12 -m unittest discover -s tests -q
if errorlevel 1 (
    echo ERROR: Regression tests failed. Do not build or distribute this beta.
    exit /b 1
)
py -3.12 -c "import sys; sys.path.insert(0,'editor'); import app, piano_roll, drum_editor, xg_part_editor; print('GUI module imports OK')"
if errorlevel 1 (
    echo ERROR: GUI module import failed.
    exit /b 1
)
py -3.12 -c "import mido, rtmidi; print('MIDI backend imports OK')"
if errorlevel 1 (
    echo ERROR: MIDI dependencies missing. Install with: py -3.12 -m pip install ""mido>=1.3,<2"" ""python-rtmidi>=1.5,<2""
    exit /b 1
)
echo Automated checks passed.
echo NEXT: Test MIDI input/output, recording, playback, loop, mixer and XG SysEx on Windows.
exit /b 0
