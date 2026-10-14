# Stage 57 – Block B, GUI XG Part mapping

- MIDI Mixer has **Map Parts...** for 16 explicit MIDI channel -> XG Part / device assignments.
- XG snapshots and playback automation follow use the selected mapping instead of assuming Part = channel.
- The mapping is shared by mixer windows in the current application session; no SMF edits occur when changing it.
- Validation rejects incomplete mappings, invalid Part/device numbers, and booleans.
- Limitations: mapping is not persisted across restarts; physical multiport XG SysEx routing and automatic synchronization of all open editor windows remain to be implemented and hardware-tested. The mixer still writes standard CC on Apply, not XG SysEx.
- Staff Editor paused; no Git operations.
