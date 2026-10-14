# Stage 17 – Yamaha XG effect parameter snapshot

Added `effect_parameters_at_tick(song, tick, device=0, effect=None)` to read the latest known raw Reverb, Chorus and Variation parameter values through a selected song tick. Values are scoped by XG device and effect, without mutating the song or assuming hardware-specific parameter names. This is groundwork for GUI parameter loading; it does not read the hardware or implement full preset editing.

Five regression tests cover time boundaries, device isolation, empty state, invalid inputs, and effect filtering. Test command: `PYTHONPATH=editor:src python -m unittest discover -s tests -q` (426 passed).

No changes to Staff Editor; no Git commits or remote operations.
