# Stage 56 – Block B continued

- Mixer now supports selecting Yamaha XG device 0–15 for XG-aware snapshots.
- During playback, XG-aware mixer mode follows CC and XG SysEx, preserving locally edited faders via existing follow_automation behavior.
- Added pure explicit channel-to-Part/device snapshot helper, avoiding the unsafe assumption that MIDI channel always equals XG Part.
- Five regression tests for mapping, device isolation, timing and validation.

## Still outstanding

Full block B is **not yet complete**: graphical assignment editor for mapping, per-port XG SysEx routing, live bidirectional window notifications, device-level automation chase, exhaustive MU1000/MU2000 effects and hardware tests. No actual MIDI device integration was tested.
