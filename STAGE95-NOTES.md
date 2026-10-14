# XGW Next — Stage 95

- File > Compare two XWS S4WT files...: read-only comparison of two Yamaha XGworks project files.
- Fixed metadata offsets 0–31 compared byte-for-byte per positionally aligned sequence track.
- Track name and variable-length region reported separately, with no unverified mixer interpretations.
- Differing MIDI track counts and truncated metadata rejected.
- 5 new tests; total 857 passed and 83 subtests passed.
- Staff editor deferred; no Git operations.
