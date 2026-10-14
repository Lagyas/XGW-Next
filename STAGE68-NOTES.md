# Stage 68 – Clip region consistency

- Batch clip edits invalidate explicit clip boundaries on affected tracks when content moves or is copied, avoiding stale or incorrectly persisted sidecars.
- Reject shared MIDI event references across multiple selected regions before mutation.
- Correct Track View status message: regions persist in the `.xgwclips.json` sidecar on Save.
- Add regression tests for region invalidation, cross-track edits and zero-offset no-op.

## Remaining Block C work
This is **not** a complete closure of Block C. Piano Roll / Drum Editor advanced tools, consistent editor-wide selection/playhead synchronization, and interactive Windows GUI validation remain unverified or incomplete. Invalidating regions is a safe fallback, not full preservation of region identity across edits.
