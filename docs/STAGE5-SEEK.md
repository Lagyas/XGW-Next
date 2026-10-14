# Stage 5 – safe transport seek

- Seek validates the target and active L/R loop before stopping current playback.
- Invalid seek positions no longer interrupt playback or silently clamp to zero.
- The first leg can start before L, but cannot start at/after R.
- Five regression tests added; 374 unittest tests pass with `PYTHONPATH=editor python -m unittest discover -s tests -q`.
- MIDI hardware and Windows GUI remain unverified. No Staff Editor changes.
