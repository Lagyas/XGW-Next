# Stage 65 – Close gap between adjacent arrangement clips

- Added `editor/clip_join.py`: validated `close_clip_gap()` moves the following inferred clip left to the end of the selected clip, with an optional gap smaller than one bar.
- Preserves existing MIDI note content and optionally moves CC/Program/Pitch Bend/Aftertouch/SysEx through the shared batch clip editing mechanism. Meta events remain at their original ticks.
- Added a Track View clip dialog button, prevalidation on a copy, and Undo support.
- Six regression tests cover merging, configurable gap, controller opt-out and invalid input atomicity.
- **Limitation:** MIDI clips are inferred from note gaps, not persistent objects. This is a gap-closing join, not a full persistent clip merge. Windows GUI and physical MIDI hardware have not been tested.
