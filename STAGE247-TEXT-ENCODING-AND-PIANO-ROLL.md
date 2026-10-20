# Stage 247 — text encoding and Piano Roll editing (2026-10-20)

Reported on macOS (applies to all platforms).

## Text encoding (Beta 1 Fix 9)
- MIDI text meta events (track names, text, copyright, lyrics, markers, cue)
  were decoded as Latin-1, so Czech names from Windows-1250 files were wrong.
- New View ▸ Text encoding: Windows-1250 (default), Windows-1252, Latin-1,
  Shift-JIS, UTF-8. Saved in preferences (`text_encoding`). Display only — MIDI
  bytes are never re-encoded. `midi.decode_text` / `encode_text` / `set_text_encoding`.
- Tests: `tests/test_text_encoding.py`.

## Piano Roll (Beta 1 Fix 10)
- Note grabbing: hit test from the click position and the note list
  (`note_at`, 3 px tolerance) instead of the pointer position and a 1-pixel
  canvas probe that missed on macOS / Retina.
- Vertical moves: sideways jitter below 10 px is ignored while dragging mostly
  vertically (`drag_delta`); the view scrolls when dragging near the top/bottom.
- Opens centred on the track's note range.
- Shortcuts: Command (macOS) and Control — Z undo, Shift+Z / Y redo, A select
  all, D duplicate, **C copy, X cut, V paste** (at the song position, snapped);
  Backspace deletes. macOS right button (Button-2) for the selection box and
  CC menu. Undo/Redo shortcuts also in the main window (not inside text fields).
- Tests: `tests/test_beta1_fix10_piano_roll_editing.py`.

## Track selection after Undo / Redo (Beta 1 Fix 11)
- From the Stage 246 checklist: after Undo of "Move track" the Tracks selection
  stayed on the row number instead of following the moved track.
- Undo snapshots now also store the selected track; Undo / Redo reselect it
  (`App._capture_history_state`, `App._reselect_track`).
- Test: `tests/test_stage229_project_undo_state.py::test_undo_redo_selection_follows_moved_track`.

Suite: 1198 passed, 9 skipped. GUI behaviour on macOS still to be confirmed by the user.

## Lyrics / Karaoke editor (Beta 1 Fix 12)
- View ▸ Lyrics / Karaoke Editor and Window ▸ Lyrics (`editor/lyrics_editor.py`,
  logic in `editor/lyrics_ops.py`).
- Lists the lyric events (FF 05) of a track with bar:beat:tick; insert at the song
  position, edit text/position, move to the song position, delete — all undoable.
- Song text box: words by spaces, syllables by "-", a new line → "/", an empty
  line → new page "<" (XF; ".kar" "\" pages are read too). "Assign syllables to
  notes" places them on the distinct note starts of a melody track from a
  position (optionally replacing lyrics in that range). "Load current lyrics"
  turns existing lyrics back into editable text.
- Karaoke view follows the song position: current page, sung syllables orange.
- Text is stored in the selected text encoding (default Windows-1250).
- Tests: `tests/test_lyrics_ops.py`; GUI smoke test on Windows (assign 16
  syllables, Czech diacritics, karaoke highlight, undo).
