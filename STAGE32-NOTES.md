# Stage 32 — Stop cursor snapshot

- Centralized tempo-map/loop-aware cursor snapshot in `editor/transport_snapshot.py`.
- Transport Stop captures cursor at the moment of stopping, rather than relying on the last 80 ms UI update. Stop also updates the next playback start tick and sequencer playhead.
- The periodic playhead refresh uses the same pure calculation as Stop.
- Added six regression tests covering absent clock, between-frame stop, early clock, loop wrap, loop progress, invalid timestamp.
- Pause remains unsupported; physical MIDI output timing and Windows GUI need interactive verification.
- Staff Editor untouched; no Git operations.
