"""Regression: equal-tick/order MIDI events must not compare Event objects."""
from midi import Song, Track, Event
from xg_mixer_bridge import combined_part_values


def test_equal_tick_and_order_cc_events_are_stable():
    song = Song(1, 480, [Track([
        Event(0, 0xb0, bytes([7, 90])),
        Event(0, 0xb0, bytes([7, 110])),
    ])])
    values, sources = combined_part_values(song, 1, 1, 0)
    assert values['Volume'] == 110
    assert sources['Volume'] == 'CC'


def test_equal_tick_and_order_across_tracks_is_stable():
    song = Song(1, 480, [
        Track([Event(0, 0xb0, bytes([7, 90]))]),
        Track([Event(0, 0xb0, bytes([7, 110]))]),
    ])
    values, _ = combined_part_values(song, 1, 1, 0)
    assert values['Volume'] == 110
