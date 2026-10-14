import pytest
from midi import Song, Track, Event, MidiError
from piano_cc_ops import insert_cc


def test_insert_and_replace_cc_preserves_other_events():
    note = Event(0, 0x90, bytes((60, 90)))
    song = Song(1, 480, [Track([note])])
    assert insert_cc(song, 0, 120, 64, 127, 2)
    assert song.tracks[0].events[-1].status == 0xB1
    assert song.tracks[0].events[-1].data == bytes((64, 127))
    assert not insert_cc(song, 0, 120, 64, 0, 2)
    assert len(song.tracks[0].events) == 2
    assert song.tracks[0].events[-1].data == bytes((64, 0))
    assert song.tracks[0].events[0] is note


@pytest.mark.parametrize('tick,cc,value,channel', [(-1, 1, 1, 1), (0, 128, 1, 1), (0, 1, -1, 1), (0, 1, 128, 1), (0, 1, 1, 17)])
def test_invalid_cc_is_atomic(tick, cc, value, channel):
    song = Song(1, 480, [Track([])])
    with pytest.raises(MidiError):
        insert_cc(song, 0, tick, cc, value, channel)
    assert not song.tracks[0].events
