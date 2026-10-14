# Stage 97 — controlled XWS comparison evidence

Compared original `A Dream of a Dream(1).XWS` with `A Dream of a Dream_2.XWS`.
- Both contain 24 S4WB tracks and 101 S4WT records; **no S4WT records changed**.
- S4WB sequence track 4 (one-based) contains CC7, MIDI channel 1 (zero-based 0), tick 495, value **110 -> 80**.
- Three 4-byte trailing chunks SCRS, SCRA, SCRD were added by XGworks, accounting for +36 bytes with headers.
- No undocumented mixer metadata mapping is asserted. The CC7 event is an existing MIDI event, not proof of a separate mixer field.
- Added read-only binary/chunk/MIDI CC evidence comparison with 5 tests.
- Full suite: 866 passed, 4 skipped, 83 subtests passed.
- No GUI hardware test, no Git operations, staff editor unchanged.
