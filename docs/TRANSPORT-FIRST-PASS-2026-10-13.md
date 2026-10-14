# Transport MIDI first-pass fix

The loop playback worker now schedules the initial pass from the actual transport cursor to R, then repeats the full L-R timeline. This aligns MIDI event scheduling with the existing UI clock model. Three regression tests cover cursor before L, at L and between L/R.

Validation: `PYTHONPATH=editor python -m unittest discover -s tests -q` (366 passed).

Known follow-up: metronome events in loop mode still use the L-R window on the first pass; live MIDI device and Windows GUI integration have not been tested.
