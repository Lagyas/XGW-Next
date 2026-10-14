# Stage 234 — Atomic Sequencer track reorder

- Stage complete track order and all associated routing/XWS/Mute/Solo metadata before modifying the live project.
- Reject invalid routes without creating Undo history or partially changing MIDI tracks.
- Commit the staged tracks and metadata as one Undo operation and refresh Sequencer, Event List and open editors.
- Added two focused regression tests for valid reorder and invalid metadata rollback.
- Windows EXE and physical MIDI devices are not tested here; Stage 235–250 remain outstanding.
- No Git commits or pushes.
