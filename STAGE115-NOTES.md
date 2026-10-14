# Stage 115 — MIDI export integrity

- Validate event status, meta type, channel-message payload size and data bytes before SMF serialization.
- Raise MidiError rather than leaking IndexError/ValueError or emitting malformed MIDI.
- Preserve existing valid SysEx, tempo and channel events; regression round-trip coverage.
- Staff Editor paused; no commit or push.
