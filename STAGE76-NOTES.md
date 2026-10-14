# Stage 76 – MIDI event identity during move/copy

- Moving events or clips between tracks preserves the existing event UUID.
- Duplicating events or clips assigns new UUIDs, preventing collisions with originals.
- Applies to batch Event List operations, batch clips, and legacy single clip operations.
- Six regression tests cover move and copy behavior.
- Remaining limitations: durable independent clip UUIDs are not implemented; UUIDs are not stored in SMF; GUI and physical MIDI tests remain outstanding.
- Block C is not certified complete until those limitations are resolved.
