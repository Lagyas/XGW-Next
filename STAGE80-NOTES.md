# Stage 80 — GUI integration and XG mixer ordering

- Added real Tk integration test under Linux Xvfb: open Piano Roll, Drum Editor, Event List, MIDI Mixer, and XG Part Editor simultaneously; exercise Undo/Redo, close/reopen Piano Roll.
- Fixed `combined_part_values` crash when MIDI events share tick, track, and order. Original event index is now a deterministic tie breaker; no comparisons between Event objects.
- Added two focused regression tests for same-tick/order events.
- Full suite: 788 passed, 83 subtests passed. Python compileall succeeded.
- Limitations: Linux virtual-display smoke is not equivalent to Windows/macOS GUI interaction or physical MIDI device verification. Block C cannot yet be hardware-certified.
- Staff Editor remains deferred; no Git operations.
