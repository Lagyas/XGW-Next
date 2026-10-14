"""Stage 235: refreshing views must not erase same-track note selection."""
from unittest.mock import Mock
from app import App


def make_app(track_index=1, selected_track=1, has_tracks=True):
    app = object.__new__(App)
    app.song = Mock(tracks=[Mock(), Mock()]) if has_tracks else None
    app.selected_track = Mock(return_value=selected_track)
    piano = Mock()
    piano.track_index = track_index
    piano.selected_pairs = {(3, 4)}
    piano.selected = 0
    piano.winfo_exists.return_value = True
    app.workspace = Mock(windows={'Piano Roll': piano})
    app.notify_midi_editors = Mock()
    return app, piano


def test_same_track_refresh_preserves_selection():
    app, piano = make_app()
    App.refresh_open_editors(app)
    assert piano.selected_pairs == {(3, 4)}
    assert piano.selected == 0
    piano.render.assert_called_once()


def test_track_switch_discards_stale_selection():
    app, piano = make_app(selected_track=0)
    App.refresh_open_editors(app)
    assert piano.selected_pairs == set()
    assert piano.selected is None
    assert piano.track_index == 0


def test_no_song_closes_stale_piano():
    app, piano = make_app(has_tracks=False)
    App.refresh_open_editors(app)
    piano.destroy.assert_called_once()
    piano.render.assert_not_called()
