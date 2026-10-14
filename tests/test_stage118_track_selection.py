"""GUI selection sync regression without a display server."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from app import App

class TrackSelectionTests(unittest.TestCase):
    def test_arrangement_selection_updates_tree_and_arrangement(self):
        app = App.__new__(App)
        app.song = Mock(tracks=[Mock(), Mock(), Mock()])
        app.tracks = Mock()
        app.sequencer = Mock()
        app.show_events = Mock()
        app.select_sequencer_track(2)
        app.tracks.selection_set.assert_called_once_with('2')
        app.tracks.see.assert_called_once_with('2')
        app.sequencer.select_track.assert_called_once_with(2)
        app.show_events.assert_called_once()

    def test_invalid_arrangement_selection_ignored(self):
        app = App.__new__(App)
        app.song = Mock(tracks=[Mock()])
        app.tracks = Mock()
        app.sequencer = Mock()
        app.show_events = Mock()
        app.select_sequencer_track(5)
        app.tracks.selection_set.assert_not_called()
        app.sequencer.select_track.assert_not_called()
