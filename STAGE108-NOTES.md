# Stage 108 – Real XWS to MIDI format 1 export regression

- Added end-to-end reference regression tests for XGworks 3, XGworks 4, and channel-changed XWS files.
- Compare all non-track-name/non-End-of-Track MIDI events after export and reimport, including tick, status/channel, payload and meta type.
- Verify output SMF format 1, time division, channel separation, and event counts.
- Confirm XGworks 3 vs XGworks 4 re-save has identical musical content.
- Reference fixtures are optional external files; tests skip when unavailable.
- Exported an actual sample MIDI file from the supplied XGworks 4 project for manual inspection.
- Test result in current environment: 916 passed, 4 skipped, 113 subtests passed.
- No routing applied to SMF export; no GUI/hardware test; no Git operations.
