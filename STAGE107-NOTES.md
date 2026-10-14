# Stage 107 – MIDI export regression and demix naming

- Mixed source tracks are exported as separate channel-specific SMF1 tracks.
- Split channel tracks receive descriptive track names (`Original [ch N]`).
- Original source meta events, timing, SysEx and channel data are retained; generated track names are additional metadata.
- MIDI output routing does not change the channel status bytes in exported MIDI.
- Reference `A dream of a dream.MID`: format 1, 18 tracks, 10959 events; exported 18 tracks, identical non-name/non-EOT event multiset and zero mixed-channel tracks.
- Tests: 912 passed, 4 skipped, 113 subtests passed (`PYTHONPATH=editor python -m pytest -q`).
- No GUI/hardware testing, Git commits or pushes.
