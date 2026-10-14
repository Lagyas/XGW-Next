# Stage 45 — Batch MIDI clip editing

- Added `editor/batch_clip_ops.py`: atomic move/duplicate of multiple arrangement clips (including clips across tracks), using the original clip boundaries throughout the operation. Moves preserve note pairs and leave CC, SysEx and tempo events untouched.
- Added Edit > Batch move/copy clips... dialog. Enter 1-based `track:clip` pairs such as `1:1, 1:2, 3:1`, choose beat offset and Move or Duplicate. Single Undo snapshot for the whole batch.
- Added 8 tests for multiple clips, duplication, inter-track routing and invalid-input atomicity.
- 588 tests + 68 subtests pass. Python compileall succeeds.
- GUI interactive Windows and MIDI hardware verification deferred; Staff Editor unchanged; no Git operations.
