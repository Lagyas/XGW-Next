# Stage 46 – Multi-selection in Track View

- Ctrl+click toggles a clip in the selection; Shift+click extends selection within one track.
- Selected clips are outlined in orange.
- Dragging a multi-selection moves/copies all selected clips as one atomic batch, preserving their relative track offsets. Ctrl on drop copies.
- Edit → Batch move/copy clips automatically uses the selected clips.
- Five selection regression tests; 593 tests + 68 subtests passed.

## Known limitations
- Clip selection is ephemeral and cleared when loading a new song.
- Cross-track group drags require all target tracks to exist; invalid edits are rejected without partial mutation.
- MIDI clip operations currently affect paired notes only, not controllers or SysEx.
- Interactive Windows GUI and MIDI hardware verification are deferred.
- Staff Editor unchanged. No Git commit or push.
