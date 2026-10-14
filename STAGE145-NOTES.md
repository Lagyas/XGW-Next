# Stage 145 – Piano Roll Pitch Bend

- Context menu in controller lane now offers Pitch Bend (14-bit).
- Render 14-bit events with neutral center line and drag/click editing.
- Insertion replaces an existing bend at the same tick/channel, otherwise appends a new event.
- 14-bit MIDI encoding uses LSB first, MSB second.
- Uses existing snapshot-based Undo and snap-to-grid.
- GUI requires validation on Windows; no GitHub push.
