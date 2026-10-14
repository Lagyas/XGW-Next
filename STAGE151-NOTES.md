# Stage 151 – Controller time-range selection

- Alt + left drag in a CC/Pitch Bend lane selects events whose ticks fall within the dragged horizontal interval (inclusive).
- Ctrl+Alt+drag adds events to the existing selection.
- Selection is filtered by active CC/Pitch Bend lane and chosen MIDI channel.
- A translucent blue time-range rectangle previews the interval during dragging.
- Selected events can be modified with CC −10, CC +10 and Delete CC from Stage 150.
- Selection does not change MIDI data or Undo history.
- Tests: 1024 passed, 8 skipped, 136 subtests passed (Linux headless; Windows GUI not tested).
