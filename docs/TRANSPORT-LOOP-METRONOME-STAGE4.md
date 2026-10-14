# Stage 4: loop metronome synchronization

The initial metronome pass now follows the transport cursor to R; subsequent passes follow L to R. Both sets of clicks are scheduled relative to their respective playback epochs, with tempo and meter map respected by `metronome_messages`.

Regression tests cover cursor before L, at L and within the loop. Test command: `PYTHONPATH=editor python -m unittest discover -s tests -q` (369 passing).

Not yet verified on hardware; Stop/Seek while playing and recording still need integration testing. Staff Editor unchanged. No commits or GitHub uploads.
