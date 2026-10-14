# Stage 49 — Clip automation and SysEx

- Batch clip move/copy can optionally carry CC, Program Change, Pitch Bend, Aftertouch, and SysEx events located within the clip's half-open time interval.
- Structural MIDI meta events (tempo, signatures, end-of-track and other meta events) remain in place. Unpaired note messages are not treated as automation.
- Batch clip dialog now includes a checkbox, enabled by default, for moving these events with notes. API default remains `False` for backwards compatibility.
- All validations run before mutating song tracks; multi-track changes are atomic and compatible with the existing single Undo snapshot.
- Seven new regression tests, including multi-track movement, copying, meta preservation, backwards compatibility, and error atomicity.
- Dragging a single clip continues using the legacy clip edit operation; this stage upgrades the batch dialog, not every drag pathway.
- GUI and hardware verification deferred to Windows testing. Staff Editor untouched; no Git commit or push.
