import pytest
from midi import Event, MidiError
from controller_move import move_controller_events
from test_stage150_controller_bulk import song as make_song


def test_move_selected_cc_preserves_other_events():
    song = make_song()
    song.tracks[0].events.extend([Event(100, 0xb0, bytes([7, 80])), Event(120, 0xb0, bytes([7, 90])), Event(130, 0xb0, bytes([10, 55]))])
    events = song.tracks[0].events
    indices = [len(events) - 3, len(events) - 2]
    assert move_controller_events(song, 0, indices, 7, 1, 30) == 2
    assert [events[i].tick for i in indices] == [130, 150]
    assert events[-1].tick == 130


def test_move_pitch_bend():
    song = make_song()
    song.tracks[0].events.append(Event(200, 0xe0, bytes([0, 64])))
    assert move_controller_events(song, 0, [len(song.tracks[0].events)-1], 'pitch', 1, -50) == 1
    assert song.tracks[0].events[-1].tick == 150


@pytest.mark.parametrize('delta', [-101, 0x10000000])
def test_out_of_bounds_atomic(delta):
    song = make_song()
    song.tracks[0].events.extend([Event(100, 0xb0, bytes([7, 80])), Event(120, 0xb0, bytes([7, 90]))])
    indices = [len(song.tracks[0].events)-2, len(song.tracks[0].events)-1]
    with pytest.raises(MidiError):
        move_controller_events(song, 0, indices, 7, 1, delta)
    assert [song.tracks[0].events[i].tick for i in indices] == [100, 120]


def test_reject_wrong_lane_without_changes():
    song = make_song()
    song.tracks[0].events.append(Event(100, 0xb0, bytes([10, 80])))
    with pytest.raises(MidiError):
        move_controller_events(song, 0, [len(song.tracks[0].events)-1], 7, 1, 10)
    assert song.tracks[0].events[-1].tick == 100


def test_noop():
    song = make_song()
    song.tracks[0].events.append(Event(100, 0xb0, bytes([7, 80])))
    assert move_controller_events(song, 0, [len(song.tracks[0].events)-1], 7, 1, 0) == 0
