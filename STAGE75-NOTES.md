# Stage 75 – stable event identity for cross-editor note selection

- Each MIDI Event now carries an in-memory UUID, excluded from dataclass value equality.
- UUIDs survive deepcopy and event reordering; shared Piano Roll/Drum selection follows note-on/off UUID pairs rather than stale indices.
- If events are deleted and their list indices reused, selection no longer jumps to unrelated notes.
- Legacy index-based selection calls remain supported for older integrations.
- Remaining limitation: UUIDs are not serialized in SMF or sidecar; imported MIDI receives fresh UUIDs. Duplicated event objects and operations that reconstruct events must explicitly assign new UUIDs or preserve old ones as appropriate. Full durable clip identity is separate and not yet complete.
- No GUI/physical MIDI hardware validation performed.
