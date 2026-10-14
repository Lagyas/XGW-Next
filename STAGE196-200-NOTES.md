# Stage 196–200 — Transport GUI synchronization (D7)

- Manual seek immediately updates main position label, floating Transport BBT field, Sequencer cursor and open Piano Roll.
- Locator updates tolerate closed/uninitialized floating Transport window.
- Three new headless regression tests for stopped seek, missing Transport window, and locator behavior.
- Existing playback and locator semantics unchanged; no Windows GUI/real MIDI device test performed.
- Staff Editor and separate MIDI Validator remain out of scope.
- Automated test result: 1098 passed, 8 skipped, 136 subtests passed.
