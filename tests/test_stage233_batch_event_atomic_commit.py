"""Stage 233: atomic Event List edits and no-op history semantics."""
from unittest.mock import Mock
from app import App
from midi import Song, Track, Event


def app_fixture():
    app = object.__new__(App)
    app.song = Song(1, 480, [Track([Event(120, 0x90, bytes([60, 90]))])])
    app.player = Mock(playing=False)
    app.recorder = Mock(recording=False)
    app.snapshot = Mock()
    app.show_events = Mock()
    app.refresh_open_editors = Mock()
    app.shared_note_selection = set()
    return app


def test_noop_does_not_invalidate_redo_or_mark_dirty():
    app = app_fixture()
    assert App.apply_batch_event_edit(app, [(0, 0)], 0) == 0
    assert not app.song.dirty
    app.snapshot.assert_not_called()
    app.refresh_open_editors.assert_not_called()


def test_copy_commits_once_with_new_uid():
    app = app_fixture()
    old_uid = app.song.tracks[0].events[0].uid
    assert App.apply_batch_event_edit(app, [(0, 0)], 240, duplicate=True) == 1
    events = app.song.tracks[0].events
    assert len(events) == 2
    assert events[0].uid == old_uid
    assert events[1].uid != old_uid
    assert events[1].tick == 360
    app.snapshot.assert_called_once()
    app.refresh_open_editors.assert_called_once()


def test_generator_selection_supported():
    app = app_fixture()
    assert App.apply_batch_event_edit(app, ((0, i) for i in [0]), 60) == 1
    assert app.song.tracks[0].events[0].tick == 180
