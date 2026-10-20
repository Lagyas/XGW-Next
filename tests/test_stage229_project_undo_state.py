from types import SimpleNamespace
from project_undo_state import capture, restore


def test_project_sidecar_restores_independent_values():
    app = SimpleNamespace(track_routes={1: 'Port A'}, xws_track_properties={'tracks': []},
                          muted_tracks={1}, solo_tracks={2}, muted_channels={3}, solo_channels={4})
    state = capture(app)
    app.track_routes[1] = 'Port B'
    app.muted_tracks.clear()
    restore(app, state)
    assert app.track_routes == {1: 'Port A'}
    assert app.muted_tracks == {1}
    assert app.solo_tracks == {2}
    assert app.muted_channels == {3}
    app.track_routes[1] = 'Port C'
    assert state['track_routes'][1] == 'Port A'


def test_missing_sidecar_is_compatible_with_older_history():
    app = SimpleNamespace(track_routes={0: 'Keep'}, muted_tracks={0})
    restore(app, None)
    assert app.track_routes == {0: 'Keep'}


def test_app_undo_redo_restores_track_state():
    from app import App
    from midi import Song, Track
    app = App.__new__(App)
    app.song = Song(1, 480, [Track([]), Track([])])
    app.history = []
    app.redo_history = []
    app._undo_project_state = {}
    app.track_routes = {0: 'Port A'}
    app.xws_track_properties = None
    app.muted_tracks = {0}
    app.solo_tracks = set()
    app.muted_channels = set()
    app.solo_channels = set()
    app.shared_note_selection = SimpleNamespace(clear=lambda: None)
    app.refresh = lambda: None
    app.status = SimpleNamespace(set=lambda _: None)
    app.snapshot()
    app.song.tracks.reverse()
    app.track_routes = {1: 'Port A'}
    app.muted_tracks = {1}
    app.undo()
    assert app.track_routes == {0: 'Port A'}
    assert app.muted_tracks == {0}
    app.redo()
    assert app.track_routes == {1: 'Port A'}
    assert app.muted_tracks == {1}


def test_undo_redo_selection_follows_moved_track():
    from app import App
    from midi import Song, Track
    selection = [2]
    app = App.__new__(App)
    app.song = Song(1, 480, [Track([]), Track([]), Track([])])
    app.history = []
    app.redo_history = []
    app._undo_project_state = {}
    app.track_routes = {}
    app.xws_track_properties = None
    app.muted_tracks = set()
    app.solo_tracks = set()
    app.muted_channels = set()
    app.solo_channels = set()
    app.shared_note_selection = SimpleNamespace(clear=lambda: None)
    app.tracks = SimpleNamespace(selection=lambda: [str(i) for i in selection],
                                 selection_set=lambda iid: selection.__setitem__(0, int(iid)),
                                 see=lambda _: None)
    app.sequencer = SimpleNamespace(select_track=lambda _: None)
    app.refresh = lambda: None
    app.show_events = lambda: None
    app.sync_track_editors = lambda: None
    app.refresh_open_editors = lambda: None
    app.status = SimpleNamespace(set=lambda _: None)
    # Move track 3 up to 2: snapshot is taken with the source selected.
    app.snapshot()
    app.song.tracks[1], app.song.tracks[2] = app.song.tracks[2], app.song.tracks[1]
    selection[0] = 1
    app.undo()
    assert selection == [2]
    app.redo()
    assert selection == [1]
