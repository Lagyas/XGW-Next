# Stage 176–180 – D3: MIDI interchange integrity

- Add read-only MIDI compatibility inspection (`editor/midi_compat.py`) for explicit GM, GM2, Yamaha XG and Roland GS reset messages. This detects reset declarations, not full conformance.
- Parse SMF MIDI Port meta events (FF 21 01 pp) on each track; reject malformed metadata and conflicting port changes, which cannot safely be represented by per-track routing.
- Add SMF round-trip audit of musical events, metadata, SysEx and non-MTrk extension chunks. End-of-track timing is deliberately excluded because the writer normalizes EOT.
- Integrate strict port metadata inspection into the opt-in Yamaha XG exporter; refuse ambiguous port assignments instead of producing incorrect output.
- Add nine regression tests for reset recognition, GS checksum, port metadata, SysEx/metadata/chunk roundtrip and XG port rejection.

**Scope and limitations:** This block does not add true multiport XG export or claim full GM/GS/GM2 certification. No automatic remapping of existing MIDI files. MIDI 2.0 UMP is a separate representation. Windows GUI and EXE remain untested in this environment. No Git commit or push; Staff Editor and standalone Validator remain paused.
