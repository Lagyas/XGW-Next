import pytest
from midi import Song, Track, Event, MidiError
from controller_bulk import bulk_controller_edit


def song():
    return Song(1, 480, [Track([Event(0, 0xb0, bytes([7, 20])), Event(120, 0xb0, bytes([7, 125])), Event(240, 0xe0, bytes([0, 64])), Event(360, 0xb1, bytes([7, 40]))])])


def test_cc_bulk_clamps_and_preserves_other_lanes():
    s = song()
    assert bulk_controller_edit(s, 0, [0, 1], 7, 1, 10) == 2
    assert [e.data for e in s.tracks[0].events] == [bytes([7, 30]), bytes([7, 127]), bytes([0, 64]), bytes([7, 40])]


def test_pitch_bend_bulk():
    s = song()
    assert bulk_controller_edit(s, 0, [2], 'pitch', 1, -8192) == 1
    assert s.tracks[0].events[2].data == bytes([0, 0])


def test_bulk_delete_reverse_indices():
    s = song()
    assert bulk_controller_edit(s, 0, [0, 1], 7, 1, delete=True) == 2
    assert len(s.tracks[0].events) == 2


def test_bulk_invalid_selection_atomic():
    s = song()
    before = [(e.tick, e.status, e.data) for e in s.tracks[0].events]
    with pytest.raises(MidiError):
        bulk_controller_edit(s, 0, [0, 3], 7, 1, 20)
    assert before == [(e.tick, e.status, e.data) for e in s.tracks[0].events]


def test_noop_keeps_clean():
    s = song()
    assert bulk_controller_edit(s, 0, [0], 7, 1, 0) == 0
    assert not s.dirty
