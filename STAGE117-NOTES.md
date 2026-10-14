# Stage 117 — Windows beta preflight

- `windows-beta-check.bat` now explicitly requires Python 3.12, matching the build script.
- Checks Tkinter, regression suite, GUI imports, and the MIDI runtime backend (`mido` and `rtmidi`) before beta distribution.
- Actionable errors and nonzero exit codes when a prerequisite fails.
- Build script verifies the EXE actually exists before reporting success.
- Regression suite verified on Linux; Windows GUI, MIDI hardware and PyInstaller executable remain untested and require a Windows 11 run.
- No Git commit or push; Staff Editor paused.
