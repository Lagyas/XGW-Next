# Block D1 – Stages 167–170: Yamaha XG export

Based on Yamaha *Recommendations for Producing XG Song Data* v2.01 (XGX-9903R, 1999).

- **167 / setup:** use opening time signature to calculate the setup measure, instead of always inserting four quarter notes; reject too-short setup measures.
- **168 / part setup:** place Bank Select MSB (CC0), Bank Select LSB (CC32), Program Change and initial CC values at separate ticks in the setup measure; preserve explicitly provided initial values, with last initial CC value winning; add default CC11=127, CC7/91/93/94.
- **169 / effects:** generate XG System On plus XG effect-type parameter-change messages for Reverb, Chorus and Variation; preserve existing initial effect type messages rather than duplicating them. Effect parameters beyond these type selectors, including reverb time, are not yet automatically generated.
- **170 / regression:** added six tests for non-4/4 meter, bank/program ordering, effect SysEx, preserving existing effects, rejecting ambiguous multiport and short measure, and SMF0/SMF1 roundtrip.

Test suite: **1059 passed, 8 skipped, 136 subtests passed** (`PYTHONPATH=editor python -m pytest tests -q`).

## Known limits

- This is an opt-in export profile, not a Yamaha XG certification. It does not yet guarantee the complete required effect parameters (notably Reverb Time), model-specific XG Level voice maps, timing separation of all note/CC/SysEx interactions, or full RPN/NRPN normalization.
- MIDI port mapping for more than 16 parts is not implemented. Nonzero or ambiguous MIDI port metadata are rejected to avoid silent misrouting.
- Initial controller/program events are treated as setup. Songs that intentionally begin with performance automation at tick zero should be reviewed after export.
- The GUI has not been exercised on Windows in this environment.
- No Git commit or push. Staff Editor paused. Validator project paused.
