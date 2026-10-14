# Stage 228 — Sequencer / Mixer track-order consistency

- Fixed Mute/Solo index remapping on insert-style track moves. Prior logic swapped source/destination indices and assigned wrong flags to intermediate tracks.
- New `track_order_ops.remap_track_indices` uses the same permutation as `move_track`.
- Added four regression tests for forward/backward/no-op/invalid moves.
- Automated suite: 1117 passed, 8 skipped, 136 subtests passed.
- Windows EXE and MIDI hardware remain untested. No Git commit or push.
