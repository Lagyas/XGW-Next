# Stage 12 – Mixer controller automation follow

Mixer Volume/Pan and other CC controls now follow the song's current playback tick, without replacing unsaved user edits. Synchronization uses the existing `channel_values` event ordering. This is a UI display synchronization, not recording automation from live faders. Playback hardware/GUI testing remains pending.

Tests: `PYTHONPATH=editor python -m unittest discover -s tests -q` – 404 passed.
No changes to Staff Editor; no Git operations.
