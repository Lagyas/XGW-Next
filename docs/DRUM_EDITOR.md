# Drum Editor (experimental)

Open a MIDI file, select a track, then choose
**View → Drum Editor (selected track)...**.

The Drum Editor displays the generic GM percussion note map (MIDI
pitches 35–81), with named rows and a horizontal beat grid.

- Choose the MIDI channel (default 10).
- Click a drum hit to select it.
- Double-click an empty row on the grid to insert a hit quantized to 1/16.
- Use **Insert hit...** to enter an exact start tick and drum note.
- Use **Move selected...** to change position or pitch.
- Use **Delete selected** to remove a note pair.
- Use **Velocity...** to set the selected hit velocity (1–127).
- Use **File → Save As** in the main editor to save changes.

The implementation reuses the Piano Roll's note pairing and editing
operations, so its changes appear in the same MIDI track and undo
history. It does not yet offer velocity bars, a kit-specific XG drum
map, step-sequencer playback, note audition, or pattern editing.

**Important:** GM percussion names are not guaranteed to match
all custom Yamaha XG drum kits. The grid is a first prototype and
has not been validated on Yamaha hardware.
