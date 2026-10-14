import pytest
from midi import Song, Track, Event, MidiError
from controller_delete import delete_controller


def song():
    return Song(1, 480, [Track([Event(0, 0xb0, bytes((7, 100)), order=0),
                                Event(120, 0xe0, bytes((0, 64)), order=1),
                                Event(240, 0x90, bytes((60, 90)), order=2)])])


def test_delete_cc_preserves_other_events():
    s = song()
    delete_controller(s, 0, 0, 7)
    assert len(s.tracks[0].events) == 2 and s.dirty
    assert s.tracks[0].events[0].status == 0xe0


def test_delete_pitch():
    s = song()
    delete_controller(s, 0, 1, 'pitch')
    assert [e.status for e in s.tracks[0].events] == [0xb0, 0x90]


@pytest.mark.parametrize('index,lane', [(0, 10), (1, 7), (2, 'pitch'), (99, 7), (0, None)])
def test_reject_wrong_target(index, lane):
    s = song()
    with pytest.raises(MidiError):
        delete_controller(s, 0, index, lane)
    assert len(s.tracks[0].events) == 3 and not s.dirty
