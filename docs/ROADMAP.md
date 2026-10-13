# Architecture and remaining milestones

1. **Prototype 0.2:** Python/Tkinter inspection, channel-event edits, transpose, themes. C++ validator 0.1 remains available.
2. **C++ MIDI document engine:** port editable model, preserve original track bytes when possible, robust ordering for simultaneous events, undo/redo commands, SMF edge cases and fuzz testing.
3. **MIDI I/O and transport:** CoreMIDI on macOS and Windows MIDI APIs via JUCE; output selection, clock, chase, record, panic.
4. **Sequencer:** track clips, piano roll, event list, drum grid, quantize, controller lanes, tempo maps, selection tools.
5. **Yamaha XG:** separate bank/voice catalog, checksum-validated parameter SysEx encoder/decoder, multipart mixer and effect editing; verify against external module.
6. **Project formats:** research XWS using supplied file samples and observed behavior, preserve unknown blocks, add import and export only when safe.
7. **Appearance:** Classic, Modern Light/Dark; dockable windows, saved layouts, high DPI, keyboard shortcuts.
8. **Release:** standalone signed Windows/macOS builds, automated regression suite, user manual and licensing review.

Original XGworks binaries are reference material, not code to copy into the new project. Confirm licensing before using Yamaha proprietary tables or redistributing their resources.
