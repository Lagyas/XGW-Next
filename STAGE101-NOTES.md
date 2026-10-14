# Stage 101 — XWS track channel properties

Added read-only channel observations from S4WT in File > XWS track channel properties.
Values outside the observed S4WT layout remain unknown. MIDI events are never remapped.

Verification: `PYTHONPATH=editor python -m pytest -q` — 885 passed, 4 skipped, 83 subtests passed.
No GUI or MIDI hardware testing performed; no Git operations.
