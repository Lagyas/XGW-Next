"""Transport cursor snapshots shared by stop and periodic UI refresh."""
from playhead_clock import playback_cursor
from midi import MidiError
from math import isfinite


def cursor_snapshot(song, clock, now):
    """Return a tempo-aware cursor at a monotonic timestamp.

    `clock` is (monotonic_start, start_tick, loop_left, loop_right).
    Keeping this calculation separate prevents Stop from depending on the
    next scheduled GUI refresh and makes seek/restart deterministic.
    """
    if clock is None:
        return None
    started, start, left, right = clock
    if not isinstance(now, (int, float)) or not isfinite(now):
        raise MidiError('Invalid transport timestamp')
    return playback_cursor(song, start, max(0.0, now - started), left, right)
