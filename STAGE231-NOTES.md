# Stage 231 — Piano Roll duplicate transaction and editor synchronization

- Validate note duplication on a deep copy before taking an undo snapshot.
- Prevent failed duplication from mutating the song or undo history.
- Publish the changed selection and refresh Event List, Sequencer and MIDI Mixer / XG Part Editor.
- Added headless GUI regression tests for success, invalid bounds and empty selection.

This is a partial implementation, not completed Stage 230–250. Windows EXE, hardware MIDI and installer were not tested or built here. GitHub unchanged.
