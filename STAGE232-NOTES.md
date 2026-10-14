# Stage 232 — Event List batch editor integration

- Added App.apply_batch_event_edit() for validated, undoable MIDI event moves and copies.
- The Event List batch dialog uses the shared operation and refreshes open Piano Roll, MIDI Mixer and XG Part Editor views after successful edits.
- Clear stale shared note selection after batch changes.
- Reject editing during playback/recording and validate before creating Undo history.
- Three new headless regression tests for commit, invalid edits, and playback lock.

This is a partial Stage 230–250 increment, **not** a finished release candidate. Windows EXE and hardware MIDI are not tested here. GitHub unchanged.
