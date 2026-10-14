# Stage 230 — SysEx device-ID interoperability

Fixed GM/GM2 universal SysEx reset detection to accept device IDs other than 0x7F; fixed Yamaha XG reset detection to accept all Yamaha device numbers 0x10–0x1F, without matching malformed or extended payloads. Three regression tests cover positive and negative variants.

Validation on Linux: 1123 passed, 8 skipped, 136 subtests passed. Python compileall and ZIP integrity verified.

This is a partial Stage 230 delivery, NOT completed Stages 230–250. No Windows EXE build, GUI acceptance, hardware MIDI testing, installer, or release candidate certification performed. No Git commit/push.
