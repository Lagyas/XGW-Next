import pytest
from midi import Song, Track, Event, MidiError
from midi_routing import validate_routes, routed_messages


def song():
    return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64'), Event(480, 0x80, b'\x3c\x00')]),
                          Track([Event(0, 0x91, b'\x40\x64')])])


def test_two_ports_same_channel_independent():
    events = list(routed_messages(song(), {0: ('A', 0), 1: ('B', 0)}, 'A'))
    assert events[0][1:] == ('A', b'\x90\x3c\x64')
    assert events[1][1:] == ('B', b'\x90\x40\x64')


def test_original_channel_preserved():
    assert list(routed_messages(song(), {1: ('B', None)}, 'A'))[1][2][0] == 0x91


def test_time_window():
    assert len(list(routed_messages(song(), {}, 'A', 0, 480))) == 2


@pytest.mark.parametrize('routes', [{2: ('A', 0)}, {0: ('A', 16)}, {0: ('', 0)}, {True: ('A', 0)}])
def test_invalid_routes(routes):
    with pytest.raises(MidiError):
        validate_routes(song(), routes, 'A')


def test_missing_default_rejected():
    with pytest.raises(MidiError):
        list(routed_messages(song(), {}, ''))
