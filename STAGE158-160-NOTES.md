# Stage 158–160 — integration and Windows beta preparation

## Stage 158 — edit integration
- Added regression checks for CC/Pitch Bend edit, copy, SMF serialization and snapshot-based Undo/Redo semantics.
- No Windows GUI automation was run; snapshot test checks data behavior, not application keyboard dispatch.

## Stage 159 — persistence
- Added `.xgwn` save/load roundtrip for edited controllers.
- Added format-1 MIDI demix/export roundtrip check for mixed-channel controller and pitch-bend events.

## Stage 160 — stabilization / beta gate
- Added atomicity regression ensuring invalid mixed-lane selection does not change MIDI serialization.
- Run full pytest suite and compilation check before shipping.
- Windows beta still requires hands-on acceptance testing; this is a **beta candidate**, not Windows GUI certification.

### Windows acceptance checklist
1. Close running XGW Next and build with `build-local-windows.bat`.
2. Open a MIDI with notes, CC7, CC11, CC64 and pitch bend across multiple channels.
3. Verify Sequencer playhead/transport sync, L/R loop, zoom and clip drag/resize.
4. In Piano Roll verify Pencil, CC lane/channel filter, CC selection, Alt-range, Shift-ramp, drag move and Ctrl-drag copy.
5. Verify CC value +/- buttons, delete, Undo (Ctrl+Z), Redo (Ctrl+Y / Ctrl+Shift+Z).
6. Save `.mid` and `.xgwn`, reopen and compare event ticks, channels and values.
7. Confirm no crashes or lost events; report screenshots/tracebacks for any GUI issues.

GitHub unchanged. Staff Editor remains paused.
