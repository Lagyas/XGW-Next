import pytest
from midi import Song, Track, Event, MidiError
from mixer_commit import preview_mixer_commit, mixer_changes
from mixer_ops import channel_values


def sample():
    return Song(1, 480, [Track([Event(0, 0xb0, bytes((7, 90)))])])


def test_atomic_preview_does_not_mutate_source():
    song = sample()
    preview, count = preview_mixer_commit(song, 0, {1: {'Volume': 105, 'Pan': 33}}, 240)
    assert count == 2
    assert channel_values(song, 1, 240)['Volume'] == 90
    assert channel_values(preview, 1, 240)['Volume'] == 105
    assert channel_values(preview, 1, 240)['Pan'] == 33
    assert song.dirty is False
    assert preview.dirty is True
    assert Song.from_bytes(preview.to_bytes()).to_bytes() == preview.to_bytes()


def test_invalid_batch_leaves_original_unchanged():
    song = sample()
    before = song.to_bytes()
    with pytest.raises(MidiError):
        preview_mixer_commit(song, 0, {1: {'Volume': 60}, 2: {'Pan': 140}}, 0)
    assert song.to_bytes() == before
    assert song.dirty is False


def test_change_detection_multiple_channels():
    assert mixer_changes({1: {'Volume': 100, 'Pan': 20}, 2: {'Volume': 60}},
                         {1: {'Volume': 100, 'Pan': 64}, 2: {'Volume': 90}}) == {
                             1: {'Pan': 20}, 2: {'Volume': 60}}


@pytest.mark.parametrize('value', [-1, 128, True, '90'])
def test_invalid_gui_value(value):
    with pytest.raises(MidiError):
        mixer_changes({1: {'Volume': value}}, {1: {'Volume': 100}})


def test_invalid_destination_is_atomic():
    song = sample()
    with pytest.raises(MidiError):
        preview_mixer_commit(song, 9, {1: {'Volume': 40}}, 0)
    assert len(song.tracks[0].events) == 1
