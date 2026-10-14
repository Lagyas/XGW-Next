# Transport validation stage — 2026-10-13

Baseline: 350 passing tests. Current: 356 passing tests (37 subtests).

Added `editor/transport_ops.py` with independent validation of playback start and active loop locators; `app.py` now validates before invoking the MIDI player. Inactive loop fields are ignored. Invalid, reversed, or empty loop intervals and starts at/after the right locator are rejected with MidiError.

Run: `PYTHONPATH=editor python -m pytest -q` from repository root.

Still pending: transport loop-clock alignment during looping, recording UX, Track View/Mixer synchronization, XG effects/SysEx completion, Windows native hardware/GUI testing. No Git commit was created.
