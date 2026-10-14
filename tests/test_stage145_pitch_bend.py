import pytest
from midi import Song, Track, Event, MidiError
from piano_pitch_ops import insert_pitch_bend


@pytest.mark.parametrize('value,data', [(0,b'\x00\x00'),(8192,b'\x00\x40'),(16383,b'\x7f\x7f'),(129,b'\x01\x01')])
def test_pitch_bend_14_bit(value, data):
    note = Event(0, 0x90, b'\x3c\x64')
    song = Song(1, 480, [Track([note])])
    assert insert_pitch_bend(song, 0, 120, value, 3)
    assert song.tracks[0].events[-1].status == 0xe2
    assert song.tracks[0].events[-1].data == data
    assert not insert_pitch_bend(song, 0, 120, 8192, 3)
    assert len(song.tracks[0].events) == 2
    assert song.tracks[0].events[0] is note


@pytest.mark.parametrize('tick,value,channel', [(-1,8192,1),(0,-1,1),(0,16384,1),(0,8192,0),(0,8192,17)])
def test_invalid_pitch_bend_does_not_mutate(tick, value, channel):
    song = Song(1, 480, [Track([])])
    with pytest.raises(MidiError):
        insert_pitch_bend(song, 0, tick, value, channel)
    assert not song.tracks[0].events
