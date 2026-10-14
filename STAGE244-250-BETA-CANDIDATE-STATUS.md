# XGW Next — Stage 244–250 beta candidate checkpoint

## Implemented and verified in this iteration
- Stage 244: per-track MIDI IN assignments persisted in `.xgwn` project archives, including validation, backward compatibility and recovery snapshots.
- MIDI IN assignments are included in Undo/Redo snapshots and autosave change fingerprints.
- Opening a standalone MIDI file clears stale per-track MIDI IN assignments.
- Project/recovery MIDI input assignments are validated before replacing the current song.
- Added 11 regression tests for persistence, corrupt data, recovery and autosave fingerprint.
- Full automated test suite: 1172 passed, 8 skipped, 140 subtests passed.
- `python -m compileall -q editor`: passed.

## Not verified / not completed
- Stage 245–250 are NOT certified complete; further GUI, MIDI, hardware, performance and packaging verification remains.
- Windows executable was not built or run in this Linux environment.
- No physical MIDI input/output hardware was available for testing.
- No verified multiport 32/64-channel hardware playback or recording test.
- No public release approval. No Git commit or push.

## Windows acceptance
1. Run `build-local-windows.bat` from project root, confirm tests pass and `dist\\XGW-Next.exe` is produced.
2. Run `verify-windows-beta.bat`.
3. Open a `.mid`, assign MIDI OUT A1/A2/B1/B2, confirm each 16-channel group reaches the expected physical device.
4. Assign a distinct MIDI IN for two tracks, save `.xgwn`, close and reopen; verify both input labels and recording source selection.
5. Change MIDI IN, Undo and Redo; confirm correct restoration.
6. Save and reopen MIDI and XGW project, compare tracks, SysEx, bank/program, tempo, routing and XWS metadata.
7. Check Play/Stop/Record, seeking, L/R loop, edit while stopped, and safe behavior while playing.
8. Test long songs, rapid window open/close, unexpected shutdown and recovery prompt.
9. Report Windows build logs and any failures before tagging Beta 1.
