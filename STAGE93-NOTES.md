# Stage 93 — XWS S4WT track alignment

Corrected positional association of the first S4WT group with S4WB tracks, including unnamed S4WT records. Earlier code filtered unnamed entries and shifted the names of subsequent tracks. Embedded track-name MIDI events are preserved and take precedence where present. Additional S4WT groups are not used to fill unnamed tracks. This change does not guess undocumented mixer fields.

Added three regression tests, including the supplied A Dream of a Dream.XWS.
Run: `PYTHONPATH=editor python -m pytest -q`
