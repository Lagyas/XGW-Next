# Stage 59 — XG SysEx physical routing

- The XG Part Editor sends to the selected track's configured physical output, falling back to the global output.
- During routed playback, SysEx is queued to the existing playback worker, avoiding competing access to the physical port.
- Complete 7-bit SysEx payloads and active destination names are validated before enqueueing.
- The worker drains queued messages on their target port; pending SysEx is cleared when routed playback stops.
- Five regression tests cover validation, idle state, port isolation, unknown destinations and byte-copy safety.

## Outstanding Block B work

This is **not** a claim of full Yamaha MU1000/MU2000 compatibility. Model-specific effect parameter catalogs and ranges remain incomplete; full GUI cross-editor synchronization and hardware integration still need hands-on validation. MIDI output was tested using mocks, not real hardware.
