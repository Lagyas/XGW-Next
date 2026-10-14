# Stage 146 — Controller ramp (Piano Roll)

- In the lower controller lane select any CC or Pitch Bend, then Shift+left-drag from the desired start value/time to end value/time.
- The ramp uses the selected Snap interval (or a 1/16 beat fallback when Snap is Off); inserts/updates events only in the selected controller/channel.
- One undo snapshot for the entire ramp; other MIDI events remain unchanged.
- Existing single-click controller editing remains available.
- Automated tests: 996 passed, 8 skipped, 136 subtests passed. Windows GUI interaction has not been verified.
- No Git commit or push.
