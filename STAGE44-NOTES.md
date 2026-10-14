# Stage 44 – larger batch: expressive controls and multi-track quantize

- Piano Roll: editable Swing percentage and Humanize timing/velocity instead of fixed presets.
- New `editor/batch_quantize.py`: atomic multi-track transform, duplicate-track de-duplication, validation before mutation.
- Edit menu: Quantize selected tracks / all tracks at 1/16, configurable strength, single Undo snapshot.
- Tests: seven new batch tests; 580 tests + 68 subtests passing.
- Staff Editor untouched; no Git commit or push.
- Interactive GUI and real MIDI hardware validation deferred.
