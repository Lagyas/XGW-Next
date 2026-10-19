# Stage 246 — Windows beta checklist run and Beta 1 Fix 7 (2026-10-19)

## Windows checklist (Windows 10 Pro 19045, Python 3.12, PyInstaller)
Run on `a472376` (origin/main) plus the fixes below.

| Step | Result |
|---|---|
| `build-local-windows.bat` (venv, deps, tests, EXE) | OK — `dist\XGW-Next.exe` 14.9 MB |
| `verify-windows-beta.bat` | OK — 1180 passed, 9 skipped, 145 subtests (1186 passed after Fix 7) |
| EXE starts, Open MIDI (18 tracks, format 1, division 480) | OK |
| Track View, Tracks list, MIDI Events list | OK |
| Piano Roll / Drum Editor / MIDI Mixer / XG Part Editor open | OK (see notes) |
| Play / Stop (loopMIDI Port 1), position advances at song tempo | OK |
| Mixer activity LEDs light while playing, clear after Stop | OK |
| L/R loop 0–1920 wraps during playback | OK |
| Save As MIDI → reopen: 18 tracks, 10 941 events, semantically identical | OK |
| Edit ▸ Move track down, Undo, Redo | OK |
| Recovery after an unexpected close ("Recovered unsaved changes") | OK |
| Exit with unsaved changes | **FAILED → fixed (Fix 7)**: closed without asking |

Not tested (no hardware here): physical MIDI IN/OUT, multiport A1/A2/B1/B2 devices,
SysEx to a real XG device, recording from a MIDI keyboard.

### Notes
- Piano Roll opens scrolled to a high range; the Bass track's notes are below the
  visible area (vertical scroll does not follow the track's notes). Cosmetic.
- After Undo of "Move track", the Tracks selection stays on the row number,
  not on the moved track. Cosmetic.

## Beta 1 Fix 7 — ask before discarding unsaved changes
- New document fingerprint (MIDI, routing, MIDI inputs; window layout and playhead
  excluded) taken after Open MIDI / Open project / Save As / Save project.
- Exit and window close ask "Save changes to … before closing?" (Yes / No / Cancel).
  Cancel keeps the app open; No drops the recovery snapshot; Yes saves (MIDI via
  Save As, `.xgwn` via Save project) and stays open if saving is cancelled or fails.
- Opening another MIDI file or project asks the same first.
- `save_as` / `save_project` return True on success.
- Tests: `tests/test_beta1_fix7_unsaved_close.py` (6).

## CI / macOS build fixes
- `ci.yml` and `build-apps.yml` ran `unittest discover` without pytest and without
  `editor` on the path, so CI and both app builds failed since 13 Oct. They now
  install pytest and run `pytest tests -q` with `PYTHONPATH=editor`.
- macOS app is packaged `--onedir --windowed` (a proper `.app`; onefile + .app is
  deprecated by PyInstaller on macOS). Windows stays a single EXE.
- `build-local-macos.sh`: same test fix.
