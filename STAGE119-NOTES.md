# Stage 119 — Track View / Piano Roll / Mixer selection sync

- Track View selection updates an already open Piano Roll to the selected track, clears stale note selection, and redraws.
- MIDI Mixer follows the selected track only when its existing Follow Track View option is enabled.
- Refresh and track reorder propagate the selection to open editors.
- MIDI events remain unchanged by selecting a track.
- 725 unittest cases run, 2 skipped, 0 failures in this environment.
- Windows GUI/manual tests still needed. Staff Editor paused. No Git commit or push.
