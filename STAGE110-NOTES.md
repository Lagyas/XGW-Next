# Stage 110 – Atomic MIDI track reordering

- Added `editor/track_order_ops.py` with atomic track movement and remapping of per-track output routes and verified XWS source properties.
- Track event objects, timestamps, original MIDI channels and SysEx are unchanged.
- Invalid positions, routes and metadata reject before mutation; no-op does not mark project dirty.
- Six regression tests added.
- GUI integration remains for the next stage; Staff Editor paused; no Git operations.
- Verification: `PYTHONPATH=editor python -m pytest -q`: 925 passed, 4 skipped, 113 subtests passed.
