# Stage 58 – Block B: persistent XG mapping and editor synchronization

- Persist all 16 MIDI channel → (XG Part, device) assignments in user settings, validating input on both save and load. Corrupt settings revert to defaults.
- Mixer Apply refreshes the XG Part Editor; XG Part Apply refreshes the Mixer. Silent XG refresh does not open a dialog or send MIDI.
- Refresh is triggered only after a successful MIDI write; opening the editors does not modify MIDI data.
- Limitations: hardware MIDI routing for real-time XG SysEx, fully automatic refresh for all editing paths, and complete MU1000/MU2000 effect catalog remain outstanding. Therefore Block B is not fully finished.
- Windows GUI and external hardware are not yet verified.
