# Stage 8 — shared-channel monitor safety

- Live channel monitor updates now reject conflicting shared-channel track Mute/Solo instead of silently falling back to a channel-only mask that could expose muted tracks.
- Mixer checkboxes revert to the last accepted state when a live monitor change is rejected by validation or output.
- Three regression tests cover conflicting shared channels, independent channels, and stopped playback.
- Run: `PYTHONPATH=editor python -m unittest discover -s tests -q` (386 passing).
- No staff editor changes, commits or GitHub operations. Hardware playback still needs validation.
