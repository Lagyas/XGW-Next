# Stage 235 — Piano Roll selection synchronization

- Preserve Piano Roll selected note pairs during refreshes of the same track, allowing `PianoRoll.render()` to reconcile stable event identities after an edit.
- Clear stale note selection only when switching to a different track.
- Close the Piano Roll safely if the project has no tracks.
- Added three regression tests.
- Full suite: 1140 passed, 8 skipped, 136 subtests passed (Linux headless).
- Windows GUI, EXE, MIDI hardware and Stage 236–250 remain unverified/incomplete.
- No Git commits or pushes.
