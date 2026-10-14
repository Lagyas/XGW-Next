# Stage 100 — XGworks 4 compatibility and channel observations

- Accept the three observed XGworks 4 trailing chunks `SCRS`, `SCRA`, `SCRD`, in order, with exactly four zero bytes each. Older files without the trailer continue to import.
- Reject malformed, partial, repeated, or nonfinal trailers instead of silently ignoring data.
- New read-only `editor/xws_version4.py` reports the observed zero-based channel candidate in the sequence-aligned S4WT records. It does not rewrite event channels or claim that every possible XWS layout is decoded.
- Controlled samples confirm that merely saving in XGworks 4 appends 36 bytes without changing the earlier data.
- GUI and hardware validation deferred. Staff Editor unchanged. No Git operations.
- Tests: 880 passed, 4 skipped, 83 subtests passed (`PYTHONPATH=editor python -m pytest -q`).
