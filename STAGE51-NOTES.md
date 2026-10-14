# Stage 51 – readable Event List MIDI and SysEx descriptions

- Event List now displays readable controller names (including XG-related standard CC), 1-based Program Change, 14-bit Pitch Bend, and pressure events.
- Complete Yamaha XG parameter-change SysEx messages are decoded for System On, known multipart parameters and selected effect addresses. Unknown XG addresses retain hexadecimal address/data; Roland and Universal SysEx are identified without pretending to fully decode them. F7 continuations are not treated as complete messages.
- Event List allows extended row selection for the existing batch event operations. Editing still operates on one row.
- 9 new regression tests. No staff editor changes, no Git operations.
- Limitations: XG parameter name map is partial; no claim of exact parity with all original XGworks manufacturer SysEx descriptions. Windows interactive and physical MIDI hardware tests are deferred.
