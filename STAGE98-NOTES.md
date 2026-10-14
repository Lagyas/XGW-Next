# Stage 98 — controlled XWS panorama evidence

Compared `A Dream of a Dream(2).XWS` and `A Dream of a Dream_pan.XWS`.
- MIDI sequence track 4 (one-based), channel 1 (one-based), tick 495: CC10 (Pan) **64 -> 15**.
- Byte offset 1863 (zero-based) changes from 0x40 to 0x0F.
- No S4WT records changed.
- The panorama edit is represented by a MIDI CC10 event in S4WB; this does not establish an undocumented mixer metadata decoder.
- XGworks added three trailing 4-byte chunks SCRS, SCRA, SCRD (+36 bytes including headers).
- Four regression tests added for the read-only binary comparison.
- Staff editor untouched; no Git operations; hardware/GUI tests deferred.
