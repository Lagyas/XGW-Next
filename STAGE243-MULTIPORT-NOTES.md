# Stage 243 — Multiport MIDI 16/32/64 channels

- Added `editor/multiport_devices.py` to map global channel numbers 1–64 onto independent physical 16-channel MIDI output endpoints.
- Added `16/32/64 channels…` configuration in Sequencer's Track MIDI output routing dialog. Select tracks, assign physical endpoints per 16-channel bank and a global channel, then save routing.
- Reject duplicate endpoint selection, missing physical endpoints and invalid global channel numbers.
- Uses existing per-track routing and `MidiPlayer.play_routed` (separate physical output handles).
- 32 channels require two independent physical endpoints exposed by Windows/RtMidi. A single conventional MIDI port cannot transmit 32 independent channels.
- Input selection, external MIDI device enumeration, playback, physical timing, and Windows GUI remain unverified on actual Windows hardware.
- No Git commit/push. Staff Editor and standalone MIDI Validator remain paused.

## Tests
`PYTHONPATH=editor python -m pytest tests -q`: 1161 passed, 8 skipped, 140 subtests passed.
`python -m compileall -q editor`: passed.
