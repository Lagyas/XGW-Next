# Stage 19 — XG snapshot insert

The effect snapshot viewer now allows selecting one effective parameter and inserting its raw Yamaha XG SysEx value at the inspected tick into a chosen MIDI track. An explicit confirmation is required. The original snapshot remains read-only until this action; no MIDI hardware messages are sent. The insertion is additive (does not silently replace other events). Invalid values and destinations are rejected without modifying the song.

Four new regression tests cover successful insertion and atomic failure cases. GUI and hardware interaction still require manual testing.
