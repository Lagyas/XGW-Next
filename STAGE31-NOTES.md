# Stage 31 – tempo-aware transport cursor

- Extracted UI playhead timing into testable `editor/playhead_clock.py`.
- Added bounded inverse conversion from song seconds to MIDI ticks.
- Loop cursor honors partial first pass, wraps precisely at R, and repeats from L.
- Handles fractional ticks, invalid clocks and upper tick bounds.
- `App._update_playhead` now uses the shared pure clock function.
- 10 new tests: 507 passed, 68 subtests passed.

Not yet verified: interactive Windows GUI timing, real MIDI devices, Windows build. Staff Editor untouched; no Git operations.
