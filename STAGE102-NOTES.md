# Stage 102 — XWS track channel source properties

- Preserve validated read-only S4WT channel observations as optional `xws-track-properties.json` inside `.xgwn`.
- XWS import captures channel observations; project open restores them; project save retains them.
- Legacy `.xgwn` archives remain valid. Original MIDI event channels are never remapped.
- Properties are observations, not editable MIDI routing. Unsupported channels remain unknown.
- Verification: `PYTHONPATH=editor python -m pytest -q` — 890 passed, 4 skipped, 83 subtests passed.
- GUI and hardware not tested; no Git operations.
