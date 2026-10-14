# Stage 104 — Selected track MIDI properties

- Added Transport > Selected track MIDI properties for the selected sequencer track.
- Displays imported XWS source channel as read-only (known/unknown/missing).
- Allows playback output channel override 1–16 or Keep without modifying MIDI events.
- Validates route changes before applying and blocks editing during playback.
- Added editor/track_channel_properties.py and five unit tests.
- Verification: PYTHONPATH=editor python -m pytest -q: 900 passed, 4 skipped, 113 subtests passed.
- No Git operations. Windows/macOS GUI and MIDI hardware remain untested.
