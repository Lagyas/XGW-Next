# Stage 77 – Persistent MIDI event and clip identities

- Sidecar schema v2 persists UUIDs of every MIDI event, even when there are no explicit clip regions.
- Explicit clip regions have UUIDs; splitting retains the first region UUID and creates a new one, merging retains the left region UUID.
- Loading verifies MIDI SHA-256, PPQN, track/event counts, region coordinates, UUID formatting and global uniqueness before applying changes.
- Reads legacy v1 sidecars for backward compatibility.
- Two new tests for identity roundtrip and atomic rejection of duplicate IDs; existing no-region test updated to reflect persistence.
- 778 pytest tests and 83 subtests pass. GUI startup/update smoke test passed under Xvfb on Linux.

## Remaining qualification

This does NOT constitute full interactive GUI certification on Windows/macOS. Clip UUID handling during all batch edits needs further audit, and MIDI hardware remains untested. Standard SMF alone does not persist project identities; keep the .xgwclips.json alongside the .mid file.
