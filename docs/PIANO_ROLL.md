# Piano Roll — prototype

Open a MIDI file, select a track and choose **View → Piano Roll**.

- 128-note keyboard grid with beat/bar guides (4/4 guide only)
- Note-on/note-off matching by channel and pitch
- Note selection and double-click edit of pitch, start and duration
- Changes are applied to the underlying MIDI events and can be saved with **File → Save As**
- **Edit → Undo** reverses the latest note edit while the Piano Roll remains open (reopen the view to refresh after undo)

Limitations: no mouse drag yet, no insert/delete, no velocity lane, no time-signature-aware bar lines, no SMPTE grid, and no real-time synchronization across multiple Piano Roll windows. This is an early editable view, not a finished sequencer.
