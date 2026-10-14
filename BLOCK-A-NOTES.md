# Block A — Event List and SysEx improvements

- Search Event List by description, tick, event type and raw hexadecimal payload, in combination with event-category filters.
- Edit complete Yamaha XG parameter-change SysEx in the Event List (tick, device, address, payload); malformed and non-XG messages remain read-only.
- Interpret known XG effect type MSB/LSB using the shared effect catalog; label selected effect parameter ranges, Multi EQ and drum-setup address families. Unknown addresses remain visible.
- Nine new regression tests, with the existing suite preserved.

## Important limitations

This is **not** a complete Yamaha XGworks parameter dictionary: model-specific MU1000/MU2000 EQ/drum/effect semantics and value ranges still need verification against device documentation. The effect and EQ parameter labels are deliberately generic rather than inventing meanings. Real Windows GUI and MIDI hardware tests are deferred. Staff Editor and GitHub untouched.
