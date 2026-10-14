# Stage 61 — Block B: mixer mapping correctness and synchronization

- Fixed two Mixer call sites that passed `(part, device, tick)` into `combined_part_values(song, part, channel, tick, device)`, inadvertently treating device as MIDI channel and tick as time.
- Introduced `mixer_channel_snapshot(song, channel, (part, device), tick)` as a validated single entry point; used in playback-follow and reload paths.
- Updating Part mappings now refreshes the other editor; Undo and Redo refresh the MIDI Mixer and XG Part Editor.
- Added four regression tests for MIDI channel/Part/device mapping and invalid mappings.
- Tests: 689 passed, 80 subtests passed.

## Remaining before calling Block B complete

- Hardware verification with physical MIDI devices and multiport SysEx routing.
- A complete, source-verified MU1000/MU2000 effect parameter catalog (do not infer unknown ranges or names).
- End-to-end GUI verification for all editing routes and window lifecycles.

Staff Editor remains deferred. No Git operations.
