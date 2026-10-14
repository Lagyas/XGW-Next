import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event
from batch_event_ops import edit_events
from batch_clip_ops import edit_clips
from clip_ops import edit_clip


def song_with_note():
    return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64'), Event(240, 0x80, b'\x3c\x00')]), Track([])])


def test_batch_event_move_keeps_identity():
    s = song_with_note(); uid = s.tracks[0].events[0].uid
    edit_events(s, [(0, 0)], 20, destination_track=1)
    assert s.tracks[1].events[0].uid == uid


def test_batch_event_duplicate_gets_new_identity():
    s = song_with_note(); uid = s.tracks[0].events[0].uid
    edit_events(s, [(0, 0)], 20, duplicate=True)
    assert s.tracks[0].events[-1].uid != uid


def test_batch_clip_move_keeps_note_identities():
    s = song_with_note(); ids = {e.uid for e in s.tracks[0].events}
    edit_clips(s, [(0, 0)], 0, destination_tracks={0: 1})
    assert {e.uid for e in s.tracks[1].events} == ids


def test_batch_clip_copy_mints_new_identities():
    s = song_with_note(); ids = {e.uid for e in s.tracks[0].events}
    edit_clips(s, [(0, 0)], 0, duplicate=True, destination_tracks={0: 1})
    assert not ids.intersection(e.uid for e in s.tracks[1].events)


def test_single_clip_move_keeps_note_identities():
    s = song_with_note(); ids = {e.uid for e in s.tracks[0].events}
    edit_clip(s, 0, 0, 0, destination_track=1)
    assert {e.uid for e in s.tracks[1].events} == ids


def test_single_clip_copy_mints_new_identities():
    s = song_with_note(); ids = {e.uid for e in s.tracks[0].events}
    edit_clip(s, 0, 0, 0, duplicate=True, destination_track=1)
    assert not ids.intersection(e.uid for e in s.tracks[1].events)
