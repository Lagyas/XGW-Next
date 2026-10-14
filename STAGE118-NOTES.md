# Stage 118 — Track selection synchronization

- Clicking a sequencer track now selects and scrolls to the corresponding Track View row.
- Sequencer selection is updated through its public `select_track()` method, ensuring redraw.
- Refresh and track reorder also use `select_track()` rather than setting internal state directly.
- Added two headless regression tests for valid and invalid selections.
- Staff Editor remains paused. No commit or push.
