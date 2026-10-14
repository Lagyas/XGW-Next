# Stage 43 – expressive quantization batch

Added `editor/expressive_quantize.py`: atomic note-onset quantization with optional note-length quantization, swing, seeded timing/velocity humanization, selection support, and MIDI tick/velocity validation. Added Piano Roll toolbar actions (Quantize length, Swing 50%, Humanize), using existing undo snapshots. Added eight regression tests.

Current presets are fixed: Swing 50%, Humanize ±8 ticks/velocity. Adjustable dialog, track-wide multi-track operations, and detailed musical groove templates remain future work. GUI interaction and MIDI hardware have not been manually verified.

Test: `PYTHONPATH=editor python -m pytest -q` -> 573 passed, 68 subtests.
No Git operations; Staff Editor untouched.
