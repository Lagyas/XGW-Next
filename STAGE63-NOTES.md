# Stage 63 — Block C foundations

- Added `clip_boundaries.py`: note-aware split of sustained notes at a tick and crop of note endpoints within an inferred arrangement clip. Structural meta, CC and SysEx remain untouched. Operations validate before committing and support existing GUI snapshot Undo.
- Added Split/Trim actions to the single-clip Track View dialog.
- Added atomic percentage/offset velocity transform for selected paired notes.
- Added eight regression tests and MIDI serialization round-trip coverage.
- **Block C is NOT complete.** Arrangement clips are inferred from note gaps and do not have persistent boundaries, so a split cannot create two independent regions. Merge, resize handles, extended Piano Roll/Drum UI, cross-window cursor synchronization, and full GUI acceptance tests remain.
- Tests run headlessly; macOS/Windows interactive GUI and MIDI hardware remain unverified. No Git actions performed.
