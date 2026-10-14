# Stage 14 — Yamaha XG SysEx input validation

- Reject bool and float values for Yamaha XG 7-bit data and device numbers.
- Reject non-byte-sequence address/data inputs with MidiError rather than TypeError.
- Return None for malformed or non-byte SysEx wire and SMF payloads.
- Added three regression tests; suite: 413 passing (`PYTHONPATH=editor python -m unittest discover -s tests -q`).
- No changes to Staff Editor; no commits or pushes.
- MIDI hardware and Windows GUI have not been tested.
