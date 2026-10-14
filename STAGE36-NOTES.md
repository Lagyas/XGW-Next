# Stage 36 – routed loop boundary state

On each repeated pass of a routed L/R loop, restore controller/program state and notes held across L, before events located exactly at L. The player silences previous voices at R. Track selection and per-track port/channel overrides are honored.

Automated verification: 533 passed, 68 subtests passed (`PYTHONPATH=editor python -m pytest -q`).

Limitations: sustain-pedal-latched voices, synthesizer envelope phase and physical MIDI timing are not reconstructed; interactive Windows/hardware verification remains deferred. Staff Editor unchanged. No Git actions.
