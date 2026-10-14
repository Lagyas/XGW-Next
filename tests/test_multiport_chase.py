import pytest
from midi import Song, Track, Event, MidiError
from multiport_chase import chase_messages

def sample():
    return Song(1, 480, [Track([Event(0, 0xb0, b'\x07\x64'), Event(10, 0xc0, b'\x05'), Event(20, 0x90, b'\x3c\x64')]), Track([Event(0, 0xb0, b'\x07\x32')])])

def test_independent_port_channel_chase():
    assert chase_messages(sample(), {0: ('A', 0), 1: ('B', 0)}, 'A', 20) == [('A', b'\xc0\x05'), ('A', b'\xb0\x07\x64'), ('B', b'\xb0\x07\x32')]

def test_no_future_events_or_notes():
    assert chase_messages(sample(), {}, 'A', 10) == [('A', b'\xb0\x07\x32')]

def test_track_filter():
    assert chase_messages(sample(), {}, 'A', 20, {0}) == [('A', b'\xc0\x05'), ('A', b'\xb0\x07\x64')]

def test_invalid_tick():
    with pytest.raises(MidiError):
        chase_messages(sample(), {}, 'A', -1)
