# Stage 125 – Fixed track inspector and transport markers

- Track/MIDI Parts inspector is a separate overlay canvas, fixed to the left edge while the timeline scrolls horizontally (including playback follow).
- Inspector keeps track selection, M/S buttons, double-click editor access and vertical scroll synchronization.
- L locator: solid green 3px line and triangle handle; R locator: solid amber 3px line and triangle handle.
- Playhead: solid red 3px line and triangle handle.
- Existing MIDI note previews remain enabled.

Validation: `PYTHONPATH=editor python -m unittest discover -s tests -q`: 735 tests, 2 skipped, OK. GUI behavior on Windows needs manual verification.
