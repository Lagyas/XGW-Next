import pytest
from midi import Event, MidiError
from controller_transform import transform_controllers
from test_stage150_controller_bulk import song as make_song


def sample():
    song = make_song()
    song.tracks[0].events.extend([Event(100, 0xB0, bytes([7, 80])),
                                  Event(120, 0xB0, bytes([7, 90])),
                                  Event(130, 0xB0, bytes([10, 55]))])
    return song, len(song.tracks[0].events) - 3


def test_move_selected_in_time_and_value():
    song, i = sample()
    count, selection = transform_controllers(song, 0, [i, i+1], 7, 1, 40, -15)
    assert (count, selection) == (2, {i, i+1})
    assert [(song.tracks[0].events[j].tick, song.tracks[0].events[j].data) for j in selection] == [
        (140, bytes([7, 65])), (160, bytes([7, 75]))]
    assert song.tracks[0].events[i+2].data == bytes([10, 55])


def test_copy_preserves_original_and_unique_id():
    song, i = sample()
    count, selection = transform_controllers(song, 0, [i], 7, 1, 48, 2, True)
    assert count == 1 and len(selection) == 1
    copied = song.tracks[0].events[next(iter(selection))]
    assert copied.tick == 148 and copied.data == bytes([7, 82])
    assert song.tracks[0].events[i].tick == 100
    assert copied.uid != song.tracks[0].events[i].uid


def test_pitch_bend_clamps_14bit():
    song, _ = sample()
    song.tracks[0].events.append(Event(200, 0xE0, bytes([0, 64])))
    i = len(song.tracks[0].events)-1
    transform_controllers(song, 0, [i], 'pitch', 1, 0, 10000)
    assert song.tracks[0].events[i].data == bytes([127, 127])


@pytest.mark.parametrize('delta', [-101, 0x10000000])
def test_invalid_tick_atomic(delta):
    song, i = sample()
    before = [(e.tick, e.data) for e in song.tracks[0].events]
    with pytest.raises(MidiError):
        transform_controllers(song, 0, [i, i+1], 7, 1, delta, 10)
    assert [(e.tick, e.data) for e in song.tracks[0].events] == before


def test_wrong_lane_atomic():
    song, i = sample()
    with pytest.raises(MidiError):
        transform_controllers(song, 0, [i, i+2], 7, 1, 10)
    assert song.tracks[0].events[i].tick == 100


def test_noop_does_not_mark_dirty():
    song, i = sample()
    assert transform_controllers(song, 0, [i], 7, 1) == (0, set())
    assert not song.dirty
