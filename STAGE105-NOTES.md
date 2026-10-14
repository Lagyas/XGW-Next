# Stage 105 – MIDI routing persistence closure

- Verified that `.xgwn` already persists validated track output ports and channel overrides in `song.mid.xgw-routing.json`.
- Fixed project open to restore `self.xws_track_properties` from the bundled source-track metadata, avoiding stale properties from the previous song.
- Added regression coverage for channel override roundtrip, `Keep` channel roundtrip, legacy bundles without routing, and invalid channel rejection.
- Source MIDI event statuses remain unchanged by route persistence.
- Verification: `PYTHONPATH=editor pytest -q` => 904 passed, 4 skipped, 113 subtests passed.
- No Git operations. Staff Editor unchanged. GUI/hardware QA deferred.
