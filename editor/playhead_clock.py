"""Pure tempo-aware conversion of playback wall-clock time into a MIDI cursor."""
from midi import MidiError
from math import isfinite
from midi_output import tick_seconds
from transport_ops import MAX_TICK, elapsed_song_seconds


def tick_at_seconds(song, seconds, maximum=MAX_TICK):
    """Find the last tick whose tempo-map timestamp does not exceed seconds.

    Uses a bounded binary search, including exact boundaries and tempo changes.
    """
    if type(maximum) is not int or not 0 <= maximum <= MAX_TICK:
        raise MidiError('Invalid playback cursor limit')
    if not isinstance(seconds, (int, float)) or not isfinite(seconds) or seconds < 0:
        raise MidiError('Invalid playback clock')
    low, high = 0, maximum
    while low < high:
        mid = (low + high + 1) // 2
        if tick_seconds(song, mid) <= seconds:
            low = mid
        else:
            high = mid - 1
    return low


def playback_cursor(song, start_tick, elapsed, left=None, right=None):
    """Return current playhead, wrapping R to L after the first partial pass."""
    if not isinstance(elapsed, (int, float)) or not isfinite(elapsed):
        raise MidiError('Invalid elapsed playback time')
    start_seconds = tick_seconds(song, start_tick)
    left_seconds = tick_seconds(song, left) if left is not None else None
    right_seconds = tick_seconds(song, right) if right is not None else None
    target = elapsed_song_seconds(start_seconds, elapsed, left_seconds, right_seconds)
    return tick_at_seconds(song, target, right - 1 if right is not None else MAX_TICK)
