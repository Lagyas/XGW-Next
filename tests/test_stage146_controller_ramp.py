import pytest
from midi import Song, Track, Event, MidiError
from controller_ramp import ramp_points, apply_ramp


def test_forward_reverse_and_single_point():
    assert ramp_points(0, 120, 0, 127, 60, 127) == [(0, 0), (60, 64), (120, 127)]
    assert ramp_points(120, 0, 127, 0, 60, 127) == [(120, 127), (60, 64), (0, 0)]
    assert ramp_points(60, 60, 25, 50, 60, 127) == [(60, 25)]


def test_ramp_upserts_only_matching_controller():
    note = Event(0, 0x90, b'\x3c\x64')
    unrelated = Event(60, 0xB0, b'\x0a\x40')
    song = Song(1, 480, [Track([note, unrelated])])
    points = ramp_points(0, 120, 0, 127, 60, 127)
    apply_ramp(song, 0, 7, 1, points)
    apply_ramp(song, 0, 7, 1, [(60, 30)])
    assert song.tracks[0].events[0] is note
    assert song.tracks[0].events[1] is unrelated
    assert len(song.tracks[0].events) == 5
    assert [e.data[1] for e in song.tracks[0].events if e.status == 0xB0 and e.data[0] == 7] == [0, 30, 127]


def test_pitch_ramp():
    song = Song(1, 480, [Track([])])
    apply_ramp(song, 0, 'pitch', 2, ramp_points(0, 120, 0, 16383, 60, 16383))
    assert [e.data for e in song.tracks[0].events] == [b'\x00\x00', b'\x00\x40', b'\x7f\x7f']
    assert all(e.status == 0xE1 for e in song.tracks[0].events)


@pytest.mark.parametrize('args', [(-1, 5, 0, 5, 1, 127), (0, 5, 0, 5, 0, 127), (0, 5, 128, 5, 1, 127)])
def test_invalid_ramps(args):
    with pytest.raises(MidiError):
        ramp_points(*args)
