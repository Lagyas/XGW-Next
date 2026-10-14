# XGworks 4 reference comparison — stage 27

Reference inspected: user-supplied XG4.ZIP (462 entries). Source baseline: stage 26 (472 passing pytest tests).

## Verified original reference data
- `XGEditor/EfMenu.ini`: 18 sections, 175 numbered entries; 19 Reverb and 21 Chorus concrete presets. Variation is a **hierarchical menu** (group links and concrete entries), not a flat list. Treating all entries as numeric effect IDs is incorrect.
- `XGEditor/MU1000_VceList.ini`: 76 sections, 1,809 numbered entries.
- `XGEditor/MU2000_VceList.ini`: 205 sections, 2,198 numbered entries.
- Other original tables include XG voice lists, GM2, PLG expansions, mixer and drum configurations.

## Implemented in stage 27
- Read-only parser of the original XGworks INI reference tables, including Shift-JIS/CP932 decoding, numbered entries, comments and duplicate-entry validation.
- Yamaha effect menu reader with explicit handling of Variation submenu links.
- Five regression tests; 477 passing tests plus 68 subtests.
- Reference assets are **not** bundled into XGW Next; importer reads the user's own XG4.ZIP.

## Remaining work (not claimed complete)
- Map original voice/effect hierarchy to XGW Next GUI, with instrument bank/program selectors and precise model support.
- Compare Transport, Track View, Mixer and Drum/Piano Roll interactions with original XGworks running on Windows; original executable cannot be meaningfully exercised on this Linux host.
- Physical 4-port MIDI timing and Yamaha hardware tests; Windows EXE smoke test.
- Staff Editor intentionally not expanded.

No Git commit or push.
