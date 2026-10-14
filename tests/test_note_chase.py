from midi import Song, Track, Event
from note_chase import held_notes


def song(*tracks):
    return Song(1, 480, [Track(events) for events in tracks])


def test_held_note_restored_before_off():
    s = song([Event(0, 0x90, bytes((60, 90))), Event(200, 0x80, bytes((60, 0)))])
    assert held_notes(s, 100) == [(None, bytes((0x90, 60, 90)))]
    assert held_notes(s, 201) == []


def test_cursor_note_is_not_duplicated():
    assert held_notes(song([Event(100, 0x90, bytes((60, 90)))]), 100) == []


def test_zero_velocity_off():
    s = song([Event(0, 0x90, bytes((60, 90))), Event(40, 0x90, bytes((60, 0)))])
    assert held_notes(s, 100) == []


def test_routed_override():
    s = song([Event(0, 0x91, bytes((64, 80)))])
    assert held_notes(s, 50, {0: ('B', 5)}, 'A') == [('B', bytes((0x95, 64, 80)))]


def test_overlapping_notes_fifo():
    s = song([Event(0, 0x90, bytes((60, 60))), Event(10, 0x90, bytes((60, 100))),
              Event(20, 0x80, bytes((60, 0)))])
    assert held_notes(s, 30) == [(None, bytes((0x90, 60, 100)))]


def test_track_and_channel_filter():
    s = song([Event(0, 0x90, bytes((60, 80)))], [Event(0, 0x91, bytes((61, 90)))])
    assert held_notes(s, 50, enabled_tracks={1}, enabled_channels={1}) == [
        (None, bytes((0x91, 61, 90)))]
