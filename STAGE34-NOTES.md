# Stage 34 — Pause/Resume held-note restoration

- Resume now optionally reconstructs notes whose Note On preceded the pause cursor and whose Note Off occurs later.
- The reconstruction is per MIDI output, channel and key, honoring track selection, channel masks and channel overrides.
- Bank/program/controller chase is sent before restored notes. Original future Note Off events release them normally.
- Regular Seek/Play behavior is unchanged; held-note restoration is enabled only when resuming Pause.
- Notes starting exactly at the cursor are not duplicated. Overlapping strikes are paired FIFO.
- Limitations: sustain/sostenuto-latched voices, SysEx-generated voices and device envelope phase cannot be faithfully resumed. GUI and hardware verification are deferred.
- Tests: 523 passed, 68 subtests passed.
- Staff Editor unchanged. No Git operations.
