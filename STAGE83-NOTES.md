# Stage 83 — Punch note-boundary handling

- New `replace_take_range_sustain_safe` repairs matched existing note-on/off pairs crossing the punch window.
- Notes crossing punch-in are cut at punch-in; notes crossing punch-out resume at punch-out; notes crossing both boundaries produce two segments.
- Untouched channels and meta/SysEx are retained. Original event identities are preserved at original outside edges; new boundary messages get fresh identities.
- Recording UI uses the new operation in Replace mode.
- Remaining: real-time MIDI input/hardware verification; XWS project import; comprehensive project recovery.
