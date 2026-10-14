# Stage 78 – Clip UUIDs across batch transfers

- Explicit region UUIDs are transferred with their clip when moving within/across tracks.
- Duplicating clips generates fresh region UUIDs.
- Region coordinates and IDs are sorted together to avoid identity drift.
- Invalid/overlapping region layouts clear both clip_regions and clip_region_ids on the affected track.
- Four new regression tests for move, copy, collision, and batch ordering.
- 782 pytest tests and 83 subtests pass.

## Limitations

Not a complete GUI certification on Windows/macOS; MIDI hardware untested. More end-to-end editing workflows still need verification before block C can be fully certified.
