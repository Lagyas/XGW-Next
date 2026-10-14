# Windows beta verification (stage 20)

This archive contains source code and a Windows build script, **not a prebuilt Windows executable**.

1. Install Python 3.12 (with Tkinter) and ensure `py` is on PATH.
2. Run `windows-beta-check.bat` to verify the Python runtime, full test suite, and GUI imports.
3. Run `build-local-windows.bat` to install MIDI dependencies and PyInstaller and build `dist\\XGW-Next.exe`.
4. Run the EXE on Windows 10/11. Check open/save MIDI, undo/redo, Track View, Piano Roll, Drum Editor, Mixer LEDs, live CC7/CC10, transport play/stop/record, seek, loop locators, XG effect snapshot editing and multi-selection Apply.
5. With a real MIDI device, test note-off after stop/mute, channel sharing, SysEx transmission and reconnect/disconnect behavior. Do not send SysEx to an unverified device.
6. Capture errors, Windows version, MIDI interface model, and reproduction steps.

No Windows executable or hardware test was performed in this Linux environment. Staff Editor is intentionally out of scope. No Git actions were performed.
