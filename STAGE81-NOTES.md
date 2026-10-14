# Stage 81 – Block D foundations

- Atomic SMF saving via `safe_save.atomic_write`: temporary file, fsync, atomic replace, and `.bak` backup on overwrite.
- `recording_ops.replace_take_range` provides a validated, non-mutating punch/replace primitive with optional channel scope, preserving meta and SysEx.
- 797 tests and 83 subtests pass.

## Remaining Block D work

- Connect punch/replace to GUI, transport L/R locators, actual recorder and undo workflow.
- Handle notes overlapping punch boundaries musically (note-on/off pairs); current low-level replacement only works on event ticks and must not be used blindly on sustained notes.
- Unified native project file format, session recovery, autosave, and XWS import are not implemented.
- Multi-file saving is not a single atomic transaction: MIDI, clip identity sidecar, and routing sidecar are separate files.
- Windows/macOS and real MIDI device tests remain deferred.
