import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from app import App


class Player:
    playing = True
    def __init__(self, fail=False):
        self.fail = fail
        self.last = None
    def set_enabled_channels(self, channels):
        if self.fail:
            raise RuntimeError('output unavailable')
        self.last = set(channels)


class ChannelMixAtomicTests(unittest.TestCase):
    def make_app(self, fail=False):
        return SimpleNamespace(player=Player(fail), song=None, muted_channels={2},
                               solo_channels=set(), muted_tracks=set(), solo_tracks=set())

    def test_rejected_output_preserves_previous_mix(self):
        app = self.make_app(True)
        with self.assertRaises(RuntimeError):
            App.set_channel_monitor_mix(app, {1}, {4})
        self.assertEqual(app.muted_channels, {2})
        self.assertEqual(app.solo_channels, set())

    def test_success_publishes_mix(self):
        app = self.make_app()
        enabled = App.set_channel_monitor_mix(app, {1}, {4})
        self.assertEqual(enabled, {4})
        self.assertEqual(app.player.last, {4})
        self.assertEqual(app.muted_channels, {1})
        self.assertEqual(app.solo_channels, {4})

    def test_invalid_input_preserves_mix(self):
        app = self.make_app()
        with self.assertRaises(ValueError):
            App.set_channel_monitor_mix(app, {True}, set())
        self.assertEqual(app.muted_channels, {2})
        self.assertIsNone(app.player.last)

    def test_stopped_player_updates_preferences(self):
        app = self.make_app()
        app.player.playing = False
        enabled = App.set_channel_monitor_mix(app, {3}, set())
        self.assertNotIn(3, enabled)
        self.assertIsNone(app.player.last)
        self.assertEqual(app.muted_channels, {3})
