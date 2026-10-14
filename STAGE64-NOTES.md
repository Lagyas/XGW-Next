# Stage 64 – Block C: Legato

- Added `legato_clip_notes` with per-channel next-onset extension, configurable nonnegative tick gap, and optional same-pitch matching.
- Preserves other MIDI events and does not shorten overlapping notes.
- Added Legato action to the Track View clip dialog, with prevalidation and Undo snapshot.
- Six regression tests cover extension, gap, same-pitch filtering, atomic validation, idempotence and SMF round-trip.
- Known limitations: inferred arrangement clips are not persistent clip regions; this is a note-level legato operation. Windows GUI and hardware validation remain outstanding. Staff Editor deferred.
