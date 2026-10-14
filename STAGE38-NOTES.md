# Stage 38 — Track View playhead follow

- Track View now follows manual transport seeks, not only playback/recording.
- Horizontal following uses a pure, bounded calculation that respects the fixed track-header column.
- Short songs and uninitialized/zero-width canvases no longer trigger scroll requests.
- Six new unit tests; GUI and MIDI hardware testing deferred by agreement.
- Staff Editor untouched; no Git operations.
