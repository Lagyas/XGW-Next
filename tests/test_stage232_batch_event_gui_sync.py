"""Stage 232: Event List batch changes must update every open editor."""
from unittest.mock import Mock
import pytest
from app import App
from midi import Song, Track, Event, MidiError


def make_app():
    app = object.__new__(App)
    app.song = Song(1, 480, [Track([Event(120, 0x90, bytes([60, 90]))])])
    app.player = Mock(playing=False)
    app.recorder = Mock(recording=False)
    app.snapshot = Mock()
    app.undo = Mock()
    app.show_events = Mock()
    app.refresh_open_editors = Mock()
    app.shared_note_selection = {(0, 'note')}
    return app


def test_batch_move_updates_views_once():
    app = make_app()
    assert App.apply_batch_event_edit(app, [(0, 0)], 120) == 1
    assert app.song.tracks[0].events[0].tick == 240
    app.snapshot.assert_called_once()
    app.show_events.assert_called_once()
    app.refresh_open_editors.assert_called_once()
    assert not app.shared_note_selection


def test_batch_invalid_is_atomic():
    app = make_app()
    with pytest.raises(MidiError):
        App.apply_batch_event_edit(app, [(0, 0)], -999)
    assert app.song.tracks[0].events[0].tick == 120
    app.snapshot.assert_not_called()
    app.refresh_open_editors.assert_not_called()


def test_batch_during_playback_is_ignored():
    app = make_app()
    app.player.playing = True
    assert App.apply_batch_event_edit(app, [(0, 0)], 120) == 0
    app.snapshot.assert_not_called()
