import pytest
from midi import MidiError, Song, Track
from multiport_devices import validate_endpoints, channel_destination, assign_global_channels


def test_32_channels_are_two_distinct_ports():
    assert channel_destination(1, ['A1', 'A2']) == ('A1', 0)
    assert channel_destination(16, ['A1', 'A2']) == ('A1', 15)
    assert channel_destination(17, ['A1', 'A2']) == ('A2', 0)
    assert channel_destination(32, ['A1', 'A2']) == ('A2', 15)


def test_64_channels_are_four_independent_banks():
    endpoints = ['A1', 'A2', 'B1', 'B2']
    assert [channel_destination(i, endpoints) for i in (1, 17, 33, 49, 64)] == [
        ('A1', 0), ('A2', 0), ('B1', 0), ('B2', 0), ('B2', 15)]


def test_routes_work_with_existing_playback_router():
    song = Song(1, 480, [Track([]) for _ in range(4)])
    routes = assign_global_channels(song, {0: 1, 1: 17, 2: 33, 3: 49},
                                    ['A1', 'A2', 'B1', 'B2'])
    assert routes == {0: ('A1', 0), 1: ('A2', 0), 2: ('B1', 0), 3: ('B2', 0)}


@pytest.mark.parametrize('endpoints', [[], ['A1', 'A1'], [''], ['A1', None]])
def test_invalid_endpoints_rejected(endpoints):
    with pytest.raises(MidiError):
        validate_endpoints(endpoints)


def test_missing_physical_endpoint_rejected():
    with pytest.raises(MidiError):
        validate_endpoints(['A1', 'A2'], ['A1'])


@pytest.mark.parametrize('channel', [0, 33, True, 1.5])
def test_invalid_global_channel_rejected(channel):
    with pytest.raises(MidiError):
        channel_destination(channel, ['A1', 'A2'])
