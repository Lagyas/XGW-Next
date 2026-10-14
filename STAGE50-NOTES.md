# Stage 50 – Unified clip editing

- Track View single-clip and multi-clip drag now share `batch_clip_ops.edit_clips`.
- Controller, program, aftertouch, pitch-bend and SysEx events within clip bounds follow dragged clips by default.
- Single-clip edit dialog includes an option to include associated events (enabled by default).
- All edits validate on a deep copy before recording an undo snapshot; changes remain atomic.
- Four regression tests added. 618 tests and 68 subtests pass.
- Structural meta events remain in place; hardware and GUI interaction still require later verification.
- Staff Editor unchanged; no Git commit or push.
