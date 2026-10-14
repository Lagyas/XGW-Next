# Stage 150 — Multi-select and bulk controller editing

- Ctrl+click in the CC/Pitch Bend lane toggles selection (orange points).
- Toolbar CC −10, CC +10, Delete CC edits selected points atomically and with a single Undo snapshot.
- 14-bit pitch bend supported, values clamped to legal range.
- Lane/channel changes clear selection. Validation checks all indices, channel and lane before mutation.
- Five focused tests. Suite: 1020 passed, 8 skipped, 136 subtests passed.
- Windows GUI not tested. GitHub unchanged; Staff Editor paused.
