# Stage 7: recording transport cursor

- Expose `MidiRecorder.current_tick()` using the capture clock and shared monotonic epoch.
- Update the transport display and sequencer playhead during live recording, including pre-roll.
- Follow the recording playhead in Track View.
- Add five regression tests for inactive, fixed-tempo, pre-roll, tempo-following and maximum-tick cases.
- Tests: `PYTHONPATH=editor python -m unittest discover -s tests -q` — 383 passed.
- No hardware MIDI or Windows UI testing performed. No Git operations performed.
