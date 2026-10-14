# MIDI 2.0 implementation status

XGW Next currently edits Standard MIDI Files (SMF) through `editor/midi.py`.
MIDI 2.0 is being implemented alongside this legacy model, **not** by changing
SMF events into UMP packets in place.

## Implemented, in memory

- `editor/midi2_ump.py`: UMP packet validation and basic MIDI 2.0 channel voice
  packet constructors. This does not provide a transport or a file format.
- `editor/midi2_bridge.py`: explicit MIDI 1.0 channel voice -> MIDI 2.0
  translation with full-range value scaling.
- `editor/midi2_sequence.py`: timed UMP events, paired MIDI 2.0 notes,
  insertion, deletion, atomic editing and selected-note quantization.
- `import_midi1_track` refuses non-channel events instead of discarding them.
  `import_midi1_channel_events` explicitly opts into skipping meta and SysEx.
  **Never use this channel-only import for a complete XG song conversion:**
  it would omit tempo, lyrics, markers and instrument SysEx.

## Not implemented

- Standard MIDI 2.0 file loading/saving, UMP timing and metadata handling.
- MIDI 2.0 endpoint discovery, negotiation, MIDI-CI, Profiles and Property
  Exchange, and live MIDI 2.0 input/output.
- Piano Roll / List Editor integration with the MIDI 2.0 sequence model.
- Per-note controller editing, registered/assignable controllers and more
  extensive MIDI 2.0 message coverage.
- Lossless conversion of an entire SMF song including meta events and SysEx.

## Developer verification

Run from the project root:

```sh
python -m unittest discover -s tests -q
python -m compileall -q editor tests
```

Do not claim MIDI 2.0 device or file compatibility on the basis of these
in-memory unit tests. Hardware and Windows GUI validation are separate tasks.
