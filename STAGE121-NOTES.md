# Stage 121 — Safe transport seek / Bezpečný přesun kurzoru

- Wait for the previous MIDI worker to release its output port before restarting playback after a seek.
- If the worker does not stop within two seconds, show a warning and do not apply the requested seek or start overlapping playback.
- Added source-level regression check; Windows MIDI hardware validation remains pending.
- Staff Editor paused. No Git commit or push.
