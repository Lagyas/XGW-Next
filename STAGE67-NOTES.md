# Stage 67 — persistent arrangement regions

- Explicit clip split/merge boundaries are persisted in `<midi>.xgwclips.json` on Save As and loaded on Open.
- The sidecar binds to the exact MIDI file via SHA-256; invalid/stale sidecars are rejected without partial application.
- Sidecar writes are atomic; plain SMF remains compatible with other sequencers.
- Six regression tests added; 731 tests and 83 subtests pass.

## Known limitations / Block C remains open

- A separate sidecar must accompany the MIDI file; exporting only MIDI loses clip regions.
- Some editing operations may leave explicit region boundaries stale; clip identity and edit semantics need further work.
- Advanced Piano Roll/Drum Editor tools, shared cursor/selection, and end-to-end GUI testing remain unfinished.
- Windows GUI and MIDI hardware not tested; Staff Editor remains deferred.
