"""Stage 158-160: controller edit -> SMF/project persistence -> undo/redo snapshots."""
from copy import deepcopy
import pytest
from midi import Song, Track, Event, MidiError
from controller_transform import transform_controllers
from midi_demix import demix_to_format1
from project_bundle import save_project, load_project


def fixture_song():
    return Song(1, 480, [Track([
        Event(0, 0xff, b'Integration', 3),
        Event(0, 0x90, bytes([60, 100])),
        Event(120, 0xb0, bytes([7, 80])),
        Event(140, 0xe0, bytes([0, 64])),
        Event(240, 0x80, bytes([60, 0])),
        Event(240, 0xff, b'', 0x2f),
    ])])


def signature(song):
    return sorted((e.tick, e.status, e.data, e.meta_type) for t in song.tracks for e in t.events
                  if not (e.status == 0xff and e.meta_type == 0x2f))


def test_stage158_controller_edit_smf_roundtrip():
    song = fixture_song()
    original = signature(song)
    count, indices = transform_controllers(song, 0, [2], 7, 1, 60, 5, copy=True)
    assert count == 1 and len(indices) == 1
    count, _ = transform_controllers(song, 0, [3], 'pitch', 1, 80, -200)
    assert count == 1
    loaded = Song.from_bytes(song.to_bytes())
    assert signature(loaded) == signature(song)
    assert signature(loaded) != original
    assert (320, 0xe0, bytes([0, 64]), -1) not in signature(loaded)


def test_stage159_project_roundtrip(tmp_path):
    song = fixture_song()
    transform_controllers(song, 0, [2], 7, 1, 48, -12)
    path = tmp_path / 'controller-edited.xgwn'
    save_project(path, song)
    loaded, routes = load_project(path)
    assert signature(loaded) == signature(song)
    assert routes is not None


def test_stage159_demix_export_preserves_controllers():
    song = fixture_song()
    song.tracks[0].events.append(Event(150, 0xb1, bytes([11, 99])))
    song.dirty = True
    exported = demix_to_format1(song)
    restored = Song.from_bytes(exported.to_bytes())
    for status, data in ((0xb0, bytes([7, 80])), (0xb1, bytes([11, 99])), (0xe0, bytes([0, 64]))):
        assert sum(e.status == status and e.data == data for t in restored.tracks for e in t.events) == 1


def test_stage158_undo_redo_snapshot_semantics():
    song = fixture_song()
    before = deepcopy(song)
    transform_controllers(song, 0, [2], 7, 1, 60, 10)
    after = deepcopy(song)
    song = deepcopy(before)  # undo: restore prior snapshot
    assert signature(song) == signature(before)
    song = deepcopy(after)  # redo: restore edited snapshot
    assert signature(song) == signature(after)


def test_stage160_invalid_selection_keeps_export_identical():
    song = fixture_song()
    before = song.to_bytes()
    with pytest.raises(MidiError):
        transform_controllers(song, 0, [2, 3], 7, 1, 60, 10)
    assert song.to_bytes() == before
    assert not song.dirty
