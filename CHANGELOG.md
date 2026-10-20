# XGW Next — changelog

Version scheme: `MAJOR.MINOR.PATCH` + beta and fix number, e.g. **0.4.0 Beta 1 Fix 13**
= git tag `v0.4.0-beta1.13`. The single source is `editor/version.py`; every
build also records its git commit and build date. Check the running version in
**Help ▸ About XGW Next…** (or the window title); **Help ▸ Copy version info**
copies it for bug reports.

When you add a fix: bump `FIX` in `editor/version.py`, add an entry here, commit
as "Beta 1 Fix N: …" and tag `v0.4.0-beta1.N`.

## 0.4.0 Beta 1

| Fix | Tag | Date | Commit | Change |
|---|---|---|---|---|
| 13 | v0.4.0-beta1.13 | 2026-10-20 | (this) | Version numbering: `version.py`, build commit/date, Help ▸ About, window title, CHANGELOG |
| 12 | v0.4.0-beta1.12 | 2026-10-20 | d65cbee | Lyrics / Karaoke editor (Window ▸ Lyrics) |
| 11 | — | 2026-10-20 | 7e30c6e | Undo/Redo selection follows a moved track |
| 10 | — | 2026-10-20 | b2e3c6f | Piano Roll: note grabbing, vertical moves, Cmd/Ctrl shortcuts, copy/cut/paste, macOS right button |
| 9 | — | 2026-10-20 | cae54a2 | View ▸ Text encoding (default Windows-1250) for names, lyrics, markers |
| 8 | — | 2026-10-20 | d9c31a9 | macOS / CI builds bundle the mido rtmidi backend (playback on macOS) |
| 7 | — | 2026-10-19 | 2503cf5 | Ask to save unsaved changes on Exit/Open; CI and macOS app build fixed |
| 6 | — | 2026-10-16 | 6a15890, 3bb2215 | MIDI clip double-click keeps Canvas items |
| — | — | 2026-10-16 | d24342a … a472376 | Track menu: Demix by MIDI Channel / Demix by Note; demix tests |
| 5 | — | 2026-10-14 | f709f75 | Open track editor from the Tracks list |
| 4 | — | 2026-10-14 | a7a6f57 | MIDI clip double-click and track panel layout |
| 1–3 | — | 2026-10-14 | b11d721 | Beta 1: MIDI multiport, GUI integration, project persistence |

Before Beta 1 the app was "XGW Next 0.3" (stages 1–243, see STAGE*-NOTES.md).
