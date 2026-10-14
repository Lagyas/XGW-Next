# Stage 16 — XG effect parameter live send

- Added `effect_parameter_message` with strict validation of effect block, offset, 7-bit data, two-byte effect type and device number.
- The effect parameter inspector can now send a selected raw parameter to the chosen MIDI output after explicit confirmation, only while playback is stopped.
- The operation does not mutate the MIDI song. Existing edit/replace functionality remains separate.
- Added four unit tests. Full suite: 421 tests passing (`PYTHONPATH=editor python -m unittest discover -s tests -q`).
- Actual MIDI hardware and Windows GUI not tested in this environment. Staff Editor unchanged. No git operations.
