"""Transport controls must not silently discard an active recording."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from app import App

class RecordingTransportGuardTests(unittest.TestCase):
    def test_stop_finishes_recording_instead_of_stopping_player_directly(self):
        app = SimpleNamespace(recorder=SimpleNamespace(recording=True), finish_recording=Mock(), player=Mock())
        App.stop_midi(app)
        app.finish_recording.assert_called_once_with()
        app.player.stop.assert_not_called()

    def test_stop_normal_playback_clears_clock(self):
        app = SimpleNamespace(recorder=SimpleNamespace(recording=False), player=Mock(), _play_clock=(1, 2, 3, 4))
        App.stop_midi(app)
        app.player.stop.assert_called_once_with()
        self.assertIsNone(app._play_clock)

    def test_play_during_recording_does_not_start_player(self):
        app = SimpleNamespace(recorder=SimpleNamespace(recording=True), player=Mock())
        with patch('app.messagebox.showwarning') as warning:
            App.play_midi(app)
        warning.assert_called_once()
        app.player.play.assert_not_called()

    def test_seek_during_recording_keeps_cursor_and_playback(self):
        app = SimpleNamespace(song=object(), recorder=SimpleNamespace(recording=True),
                              loop_enabled=SimpleNamespace(get=lambda: False),
                              loop_start=SimpleNamespace(get=lambda: '0'),
                              loop_end=SimpleNamespace(get=lambda: '100'),
                              playhead_tick=50, player=Mock())
        with patch('app.messagebox.showwarning') as warning:
            App.seek_to_tick(app, 70)
        warning.assert_called_once()
        self.assertEqual(app.playhead_tick, 50)
        app.player.stop.assert_not_called()
