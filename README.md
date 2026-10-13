# XGW Next

Cross-platform MIDI sequencer and Yamaha XG editor inspired by Yamaha XGworks V3/V4.

> **Status:** Early development. Not a complete replacement for XGworks yet.

## Goals

- Windows and macOS support
- Standard MIDI File (SMF 0/1) editing with careful preservation of SysEx and meta events
- Track View, Event List, Piano Roll, Drum Editor and MIDI Mixer
- Yamaha XG instrument banks, controller and effect parameter editing
- External MIDI device playback and recording
- Classic, Modern Light and Modern Dark interface modes
- Investigation of XGworks native XWS project compatibility

## Architecture (proposed)

- **MIDI Core:** tracks, events, timing, parsing/writing, undo/redo
- **MIDI I/O:** external ports, scheduling, playback and recording
- **XG layer:** bank/program definitions, SysEx and parameter interpretation
- **UI:** independent views backed by a common document model
- **Compatibility tests:** round-trip tests with legally supplied MIDI/XWS fixtures

The long-term target is C++17/CMake with a cross-platform GUI toolkit (JUCE under a suitable license). Earlier exploratory prototypes may use Python; these are not yet a unified production application.

## Roadmap

1. Establish source baseline and reproducible build/tests.
2. Validate SMF parsing and editing with regression tests.
3. Implement Track View and Event List.
4. Add MIDI output/playback and Piano Roll.
5. Add Yamaha XG editor and mixer.
6. Research and implement supported XWS import/export.
7. Refine Classic/Modern UI, packaging and platform tests.

## Repository policy

Do not commit proprietary Yamaha installers, executables, DLLs, copyrighted sound banks, license keys, or private music files without permission. Use independently authored definitions and small distributable test fixtures.

## License

To be decided before public distribution. Repository is private.
