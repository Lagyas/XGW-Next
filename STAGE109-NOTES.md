# Stage 109 – Preserve non-track SMF chunks during demix

- Preserve legal unknown SMF chunks and extended MIDI header bytes during format-0/1 channel demix.
- Remap chunk insertion boundaries when one source track expands into multiple tracks.
- Add three regression tests covering before, between and after track chunks and header extension.
- No MIDI output routing applied; Staff Editor untouched; no Git operations.
