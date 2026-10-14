# Stage 2: Transport playhead clock correction

- Fixed playhead clock starting at L instead of the actual playback cursor when loop is enabled.
- First pass now runs from the cursor to R, subsequent passes from L to R.
- Tempo-map tick conversion continues to use `tick_seconds`.
- Added seven focused tests covering initial partial loop, wrapping, repeated loops, pre-L start, negative elapsed time and invalid bounds.
- Run: `PYTHONPATH=editor python -m unittest discover -s tests -q` (363 tests passed).
- No Staff Editor changes. No Git commits or pushes.
