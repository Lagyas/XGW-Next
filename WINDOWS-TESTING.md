# XGW Next — Windows 10 local test guide

## Build without GitHub Actions

Requires Python 3.12 installed and internet access to install dependencies.

1. Download the latest source ZIP from the repository (Code > Download ZIP).
2. Extract to a local folder, for example `F:\\XGW-Next`.
3. Open PowerShell in that folder.
4. Run `.\\build-local-windows.bat`.
5. After all tests pass, launch `dist\\XGW-Next.exe`.

The batch file uses `py -3.12`, not the default Python 3.14. It installs dependencies in a private `.venv` folder.

## Sequencer controls

- Click a MIDI clip to open the numeric Move / Duplicate dialog.
- Drag a MIDI clip left or right to move its notes by whole beats.
- Drag a clip up or down to move its notes to another track.
- Hold **Ctrl** during drag release to copy instead of move.
- Use the mouse wheel to scroll vertically; **Shift + wheel** scrolls horizontally.
- Double-click a track to open its Piano Roll.
- Use **Edit > Undo** to revert the most recent edit.
- Use **File > Save As** to save the edited MIDI file.

Clip editing currently moves only paired note-on/note-off events. MIDI controllers, SysEx, program changes and tempo events are not moved with the clip. Clips are inferred from note gaps, not separate MIDI regions. Always test using a copy of your MIDI file.

## Rebuild after a source update

Download/extract the latest source, then rerun `build-local-windows.bat`. Building is local and does not require GitHub Actions artifact storage.
