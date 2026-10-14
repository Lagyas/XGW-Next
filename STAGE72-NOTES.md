# Stage 72 — shared editor cursor

Piano Roll and Drum Editor now accept Shift+click on their timelines to seek the shared application transport cursor. The helper converts canvas coordinates to PPQN ticks, clamps negative positions, and respects each editor's snap option. Seeking while recording is blocked. Both editors rely on the existing transport seek path, including stop/restart while playing.

This stage does **not** close Block C: editor selection sharing, complete clip identity, and GUI/hardware integration still need verification. Staff Editor untouched; no Git operations.
