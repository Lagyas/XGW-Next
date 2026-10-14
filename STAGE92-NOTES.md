# Stage 92 — XWS MIDI setup audit

- Added `track_setup_report(song)` and `format_track_setup_report(song)` to `editor/xws_import.py`.
- Reports actual MIDI channel messages: bank MSB/LSB, program (1-based UI), volume, pan, expression, reverb and chorus, plus count of SysEx events.
- Added File > XWS MIDI setup report... read-only GUI report.
- Does NOT interpret undocumented S4WT mixer data; last observed values are not necessarily the original mix state.
- Real sample A Dream of a Dream.XWS: 24 imported tracks; original file not changed.
- 845 tests, 83 subtests passed; compileall passed.
