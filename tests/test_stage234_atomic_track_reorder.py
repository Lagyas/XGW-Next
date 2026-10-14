"""Stage 234: track moves commit MIDI and project metadata atomically."""
from unittest.mock import Mock, patch
from app import App
from midi import Song, Track, Event


def fixture():
    app = object.__new__(App)
    app.song = Song(1, 480, [Track([Event(i * 120, 0x90, bytes([60+i, 90]))]) for i in range(3)])
    app.player = Mock(playing=False)
    app.recorder = Mock(recording=False)
    app.selected_track = Mock(return_value=0)
    app.snapshot = Mock()
    app.track_routes = {}
    app.xws_track_properties = None
    app.muted_tracks = {0, 2}
    app.solo_tracks = {1}
    app.refresh = Mock()
    app.tracks = Mock()
    app.sequencer = Mock()
    app.show_events = Mock()
    app.sync_track_editors = Mock()
    app.status = Mock()
    return app


def test_reorder_commits_once_and_remaps_flags():
    app = fixture()
    App.move_selected_track(app, 1)
    assert [t.events[0].data[0] for t in app.song.tracks] == [61, 60, 62]
    assert app.muted_tracks == {1, 2}
    assert app.solo_tracks == {0}
    app.snapshot.assert_called_once()
    app.refresh.assert_called_once()


def test_invalid_route_leaves_everything_untouched():
    app = fixture()
    app.track_routes = {9: {'port': 0}}
    before = [t.events[0].data[0] for t in app.song.tracks]
    with patch('app.messagebox.showerror'):
        App.move_selected_track(app, 1)
    assert [t.events[0].data[0] for t in app.song.tracks] == before
    assert app.muted_tracks == {0, 2}
    app.snapshot.assert_not_called()
    app.refresh.assert_not_called()
