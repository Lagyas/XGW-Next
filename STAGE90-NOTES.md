# XGW Next Stage 90 — Yamaha XWS MIDI import

- File > Import Yamaha XWS MIDI… imports S4WB event streams into editable MIDI tracks.
- Decodes Yamaha four-byte big-endian note duration following positive-velocity Note On, synthesizes Note Off.
- Handles VLQ delta times, MIDI running status, meta events, SysEx, channel voice messages.
- Validates XWS chunk bounds, event lengths, PPQN, maximum input size, and generated SMF.
- Verified against `A Dream of a Dream.XWS`: 24 tracks, 480 PPQN, 10,924 converted events.
- Does not reconstruct legacy mixer, clip, or window settings; does not overwrite XWS.
- Run: `PYTHONPATH=editor python -m pytest -q`.
- Staff Editor deferred; no Git changes or MIDI hardware tests.
