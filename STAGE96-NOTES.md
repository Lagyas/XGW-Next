# XGW Next — Stage 96

- Added read-only `editor/xws_experiment.py` to document controlled single-setting XWS S4WT experiments.
- Candidate byte offsets remain explicitly unverified; no guessed mixer/channel mappings are applied to imported songs.
- Detects changes in unrelated tracks and rejects invalid experimental declarations.
- Added 8 regression tests; pytest: **861 passed, 4 skipped, 83 subtests passed** (stage 95 baseline in this environment: 853 passed, 4 skipped, 83 subtests passed; previous headline 857 counted skipped tests).
- Only one XWS reference project was supplied, so no controlled before/after parameter identification was possible.
- Staff editor unchanged; no Git commands executed.
