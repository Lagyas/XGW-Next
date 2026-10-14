# Stage 144 – Piano Roll CC lane

- Click an empty CC lane to insert a controller event at the snapped tick.
- Preserve selected controller and infer MIDI channel from the track's first paired note (fallback channel 1).
- Update existing CC event with matching tick/controller/channel instead of creating a duplicate.
- Keep undo snapshot and existing drag-to-change CC values.
- Test: 981 passed, 8 skipped, 136 subtests.
- Windows GUI interaction requires manual verification.
