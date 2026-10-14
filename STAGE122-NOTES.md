# Stage 122 – Transport loop clock validation

- Hardened `elapsed_song_seconds()` to convert invalid loop locator values into `MidiError` rather than leaking `TypeError`/`ValueError`/`OverflowError`.
- Added regression coverage for partial first loop, wraparound, invalid clock values, optional/inactive loop, and L/R locator drag boundaries.
- Test run: `PYTHONPATH=editor python -m unittest discover -s tests -q` — 731 tests, OK (2 skipped).
- Staff Editor remains paused. No Git commit/push performed.
