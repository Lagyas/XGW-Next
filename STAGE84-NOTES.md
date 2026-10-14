# Stage 84 – XGW Next portable project archive

- Added `.xgwn` ZIP-based project format with `manifest.json`, `song.mid`, clip/identity and routing sidecars.
- Added File > Open XGW Project and File > Save XGW Project.
- Archive member allowlist, duplicate-name rejection, per-member uncompressed size cap, version check and staged atomic save.
- Regression tests cover roundtrip of regions and event IDs, invalid archive members, and corrupt ZIP.
- 808 tests and 83 subtests pass.

## Limitations

- `.xgwn` is a new XGW Next format, **not** an importer for Yamaha XGworks `.xws`.
- The archive does not yet persist every GUI preference, window layout or audio/MIDI device configuration.
- No automatic recovery journal or periodic backups are included yet.
- Windows/macOS interactive testing and physical MIDI hardware testing remain deferred.
