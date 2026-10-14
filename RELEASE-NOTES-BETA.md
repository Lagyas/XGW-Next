# XGW Next – consolidated beta source candidate

This package combines all stages through stage 20 with a Drum Editor improvement:
- Drum hit insertion uses the same selectable snap resolutions as Piano Roll (Off, 1/4–1/64).
- Both mouse double-click insertion and dialog insertion follow the selected grid.
- Invalid positions and grid resolutions are rejected before modifying the song.
- Five new regression tests cover the behavior.

Validation: 443 unittest cases pass on Linux with `PYTHONPATH=editor`.
This is a **source beta candidate**, not a tested Windows binary. Windows GUI, MIDI I/O and Yamaha SysEx require on-device testing using WINDOWS-BETA-CHECKLIST.md.
No Git operations performed; Staff Editor untouched.
