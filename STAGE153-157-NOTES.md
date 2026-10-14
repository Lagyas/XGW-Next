# Stage 153–157 — Controller transform block

- Stage 153: drag selected controller points to shift time on the active Snap grid.
- Stage 154: Ctrl+drag selected points to duplicate, preserving source events and generating unique MIDI event UIDs.
- Stage 155: vertical drag adjusts values (7-bit CC / 14-bit pitch bend), with clamping and combined time/value transforms.
- Stage 156: validation of complete selection, active lane and channel, all-or-nothing mutations; CC value ±1 controls.
- Stage 157: integration with application snapshot Undo and redraw; focused regression tests.
- Usage: Ctrl+click selects points; drag a selected point to move selection; Ctrl+drag a selected point copies it. Alt+drag selects time region; Shift+drag draws ramp. CC value ±1 changes selected points.
- GUI has not been manually tested on Windows. No GitHub commits/pushes. Staff Editor paused.
