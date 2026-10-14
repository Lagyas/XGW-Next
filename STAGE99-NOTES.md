# Stage 99 – controlled XWS MIDI channel experiment

Compared `A Dream of a Dream(3).XWS` (52,077 bytes) and `A Dream of a Dream_ch.XWS` (52,113 bytes).

- One changed byte in the shared prefix: absolute offset 46922, 0x00 -> 0x01.
- The byte is at payload offset 2 of the 2nd S4WT record (chunk 27, beginning at offset 46912).
- The corresponding S4WT record has the name `EX`; it aligns to sequence track 2.
- No other existing chunk changes. Three 4-byte chunks `SCRS`, `SCRA`, `SCRD` are appended (36 bytes including headers).
- This is strong evidence that S4WT prefix offset 2 is associated with the edited track's channel setting, but the channel encoding is not yet independently verified by multiple values. Do not automatically decode or apply it.
- Added read-only `editor/xws_channel_evidence.py` and four tests.
- pytest: 874 passed, 4 skipped, 83 subtests passed. No Git operations. GUI and physical MIDI tests deferred.
