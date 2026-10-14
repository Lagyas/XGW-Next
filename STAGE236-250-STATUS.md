# XGW Next — combined Stage 236–250 integration checkpoint

## Implemented and tested in this checkpoint
- SMF event editing validates tick and payload *before* mutating the event; invalid payload no longer leaves an updated tick behind.
- A no-op edit leaves the song dirty flag untouched; ticks outside the SMF VLQ range and noninteger values are rejected.
- MIDI round-trip audit now compares event sequence within each tick, not only a multiset; this protects Bank Select / Program Change and Note On/Off ordering.
- Regression tests for edited XG SysEx and MIDI port metadata, invalid event edits, roundtrip, and rejection of unsupported multiport XG export.
- `verify-windows-beta.bat` runs Windows unit-test preflight and checks the expected built EXE exists.

## Verification performed
- Linux/headless: 1146 passed, 8 skipped, 140 subtests passed.
- Python syntax compilation and ZIP integrity checked.

## NOT completed or verified
- Stage 236–240 exhaustive compatibility against real Yamaha XGworks files and hardware.
- Stage 241–245 Windows GUI/EXE launch, MIDI input/output, recording and crash recovery on actual Windows hardware.
- Stage 246–250 release candidate sign-off, installer, end-to-end UI acceptance and field validation.
- Windows build is intentionally NOT claimed to be tested here; `build-local-windows.bat` and `verify-windows-beta.bat` must be run on Windows.
- No Git commits or pushes; Staff Editor and standalone Validator remain paused.

## Windows acceptance checks
1. Run `build-local-windows.bat`, then `verify-windows-beta.bat`.
2. Launch `dist\XGW-Next.exe`; import MIDI containing GM, GS, XG SysEx and multiple MIDI ports.
3. Confirm untouched import/export is byte-identical; after edits, inspect SysEx, port metadata, program/bank ordering and note timing.
4. Edit notes in Piano Roll and Event List; check Sequencer and Mixer synchronization and Undo/Redo.
5. Test Transport Play/Stop/Record, seek, L/R loop and actual MIDI I/O with a connected device.
6. Save, close, reopen, and recover project; confirm routing, mute/solo and XWS metadata.
7. Test malformed MIDI/XWS files, missing devices and abrupt shutdown without overwriting originals.
