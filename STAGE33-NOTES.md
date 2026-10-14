# Stage 33 — Pause / Resume transport

- Added Pause / Resume to the Transport menu, main toolbar and floating Transport window.
- Pause snapshots the playhead with the tempo-aware clock, silences the MIDI worker, and preserves the tick for resume.
- Resume waits for the old MIDI worker to release its port before restarting playback at the preserved tick. Routed playback uses its existing controller chase.
- Stop clears the paused state; Play resumes when paused.
- MIDI notes are silenced at pause; sustained notes are **not** reconstructed on resume. This is a deliberate limitation, not a full sample-accurate MIDI pause.
- Physical hardware, Windows GUI and MIDI port behavior remain unverified. Staff Editor unchanged; no Git operations.
