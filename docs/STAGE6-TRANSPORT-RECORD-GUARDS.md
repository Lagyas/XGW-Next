# Stage 6 — Transport / recording safety

- Stop now finalizes an active MIDI recording using the existing finish/merge path, instead of stopping playback alone.
- Play is blocked while recording, avoiding competing playback workers.
- Seek is blocked during recording to prevent captured notes from being placed against an inconsistent timeline.
- Four regression tests cover Stop (recording and ordinary playback), Play and Seek.
- `PYTHONPATH=editor python -m unittest discover -s tests -q`: 378 tests pass.

Remaining: interactive MIDI device testing, live recording cursor clock, Windows beta validation. No Staff Editor changes.
