# Stage 62 — Block B: effect routing and edit synchronization

- All three XG effect send entry points (single parameter, effect type batch, Part settings) now honor selected track's physical output route. Effect sends during multiport playback use the existing player queue instead of reopening a busy port. A missing route or single-port playback fails safely.
- Added pure, testable effect delivery service with complete SysEx validation before opening a port or queuing messages. A failed device after a partial batch is not transactional.
- Effect parameter edits, effect type writes, snapshot single inserts and snapshot batch inserts now use the application's Undo snapshot and notify other editors after successful changes.
- Added eight regression tests covering route selection, playback queue, output mocks, validation and order.

## Limitations / outstanding verification

- Real Yamaha MU1000/MU2000 devices and physical multiport interfaces are not available in this runtime. All output tests use mocks. Hardware QA must be performed with actual devices; no physical compatibility claim is made.
- Complete model-specific MU1000/MU2000 effect parameter names, sizes, ranges and algorithm mappings cannot be asserted from the available reference archive (EfMenu.ini is a preset menu, not a complete parameter specification). Unknown values remain raw bytes to prevent misinformation or data corruption. Obtain verified Yamaha MIDI Data List manuals before extending those tables.
- Tk GUI is not exercised by headless automated tests. Cross-window live updates still require an interactive QA pass on Windows and macOS.

## Suggested hardware QA

1. Connect two MIDI outputs to two distinguishable XG-compatible modules; set different device IDs and route tracks separately.
2. Stop playback; send one effect parameter from each routed track and verify each module receives only its designated SysEx.
3. Start multiport playback; send a three-message effect type batch and verify queued order, absence of port-busy errors and resulting sound.
4. Disconnect one output mid-send and verify the UI reports an error; no silent success.
5. Write effect types, edit a parameter, apply a snapshot, then Undo/Redo and verify both XG Editor and Mixer display the same values.
6. Test effect algorithms and per-algorithm ranges against the relevant Yamaha MIDI Data List, not just the XGworks preset menu.
