# Stage 47 — Batch Event List editing

- Atomic move/copy of multiple MIDI events, including CC, program, pitch bend, aftertouch and SysEx.
- Optional destination track, validated tick offsets, preservation of source on copy.
- Structural meta events (end of track, tempo, meter, key signature) are excluded to avoid breaking global timing.
- Edit > Batch move/copy events… operates on selected Event List rows and records a single Undo snapshot.
- 8 new regression tests; GUI and hardware remain to be verified interactively on Windows.
- Staff Editor unchanged; no Git commit or push.
