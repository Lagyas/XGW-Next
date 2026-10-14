# Stage 191–195 — D6 GUI lifecycle stability

- Mixer close cancels its scheduled meter callback and is idempotent.
- Meter refresh stays scheduled when the current song is absent.
- Closed mixer does not reschedule meter refresh.
- Mixer reload guard is always reset via finally, including unexpected exceptions.
- Five headless regression tests: `tests/test_stage191195_gui_lifecycle.py`.
- Test result: 1095 passed, 8 skipped, 136 subtests passed.
- Windows GUI/EXE and physical MIDI device operation NOT verified here.
- Staff Editor and MIDI Validator unchanged; no Git operations.
