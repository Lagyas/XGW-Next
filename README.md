# XGW Next

Cross-platform MIDI sequencer and Yamaha XG editor inspired by Yamaha XGworks V3/V4.

> **Status:** Early development. Not a complete replacement for XGworks yet.

## Download a desktop test build

The [Build test applications](https://github.com/Lagyas/XGW-Next/actions/workflows/build-apps.yml)
workflow packages the Python/Tkinter prototype for Windows and macOS.

1. Open the workflow link while signed in to the private repository.
2. Open the newest successful run (or choose **Run workflow**).
3. Scroll to **Artifacts** and download **XGW-Next-Windows** or **XGW-Next-macOS**.
4. Unzip the artifact. Windows: run `XGW-Next.exe`; macOS: launch `XGW-Next.app`.

These are experimental, unsigned builds. Windows SmartScreen or macOS
Gatekeeper may warn; only proceed if you trust the source. MIDI hardware
playback and SysEx sending require a compatible connected MIDI interface.
Build artifacts expire after 14 days. GitHub Actions must be enabled in
the repository. An artifact appears only after the build succeeds.

## Which version am I running?

**Help ▸ About XGW Next…** shows the version (e.g. *0.4.0 Beta 1 Fix 13*), the
git tag (`v0.4.0-beta1.13`), the commit and the build date; the window title shows
the version and commit too. **Help ▸ Copy version info** copies it for bug
reports. All changes are listed in [CHANGELOG.md](CHANGELOG.md).

To update a local build: `git pull`, then `build-local-windows.bat` or
`bash build-local-macos.sh` — the new app then shows the new commit.

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

### Live Mixer Mute/Solo (October 2026)
Mute/Solo in the 16-channel Mixer now changes playback audibility while playing.
Disabling a channel sends sustain/sostenuto off and all-notes-off, then filters
subsequent channel MIDI messages. It does not edit the song. Live re-enabling
resumes subsequent events; notes that began while muted are not reconstructed.
Windows MIDI hardware/GUI verification is still required.

### Track View keyboard shortcuts (October 2026)

Click inside the Track View arrangement to focus it. Press **M** to toggle Mute
for the selected track, **S** to toggle Solo, or **Esc** to clear all Solo tracks.
Muted/non-soloed clips are shown in gray. Track-level Mute/Solo still requires
stopped playback; MIDI channel Mute/Solo in Mixer supports live switching.

### Current development priority (2026-10-13)
Staff Editor is on hold by request. Current work prioritizes playback safety,
Track View/Mixer integration, Yamaha XG parameter handling, and Windows testing.
Mixer multi-channel Apply now validates the full batch before changing any events.
