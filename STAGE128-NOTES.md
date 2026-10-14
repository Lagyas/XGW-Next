# Stage 128 – Piano Roll selection identity

- Preserve note selection across event reordering using stable MIDI event UIDs.
- Avoid selecting unrelated notes after deletion or index reuse.
- Keep local selection when there is no matching shared UUID selection.
- Added four focused regression tests.
- Staff Editor remains paused. No Git commit/push.
- Fixed Tk Canvas widget lift() crash when opening Track View (removed invalid canvas-item raise).
