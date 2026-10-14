# Stage 166 – opt-in Yamaha XG MIDI export

New File menu command: **Export Yamaha XG MIDI...**; XG Level 1, 2, 3.

- Non-destructive export from current Song.
- SMF0 for Level 1; demixed SMF1 for Levels 2/3.
- Inserts one 4/4 setup measure (PPQN 48–480), XG System On and baseline part CC values.
- Retains tempo/meter/key metadata at original positions; shifts performance events one measure.
- Preserves explicit initial CC values; no hidden overwrite of source.
- Rejects unsupported SMPTE and SMF2 sources.
- Tests: 1053 passed, 8 skipped, 136 subtests.

**Limitations:** Not a full Yamaha certification: does not enforce detailed effects (reverb/chorus type/time), voice maps, instrument-bank timing, CC/note separation, XG multiport metadata, or a source-dependent setup measure length. Initial bank/program sequence may need further refinement. Intended as a first-stage XG export profile, not a repair or compliance guarantee.

**Next:** standalone read-only MIDI validator for GM, GS, GM2, XG, and MIDI 2.0 (UMP). The Yamaha PDF XGX-9903R V2.01 applies specifically to XG song production; it does not specify GM/GS/GM2/MIDI2.0 validation.
