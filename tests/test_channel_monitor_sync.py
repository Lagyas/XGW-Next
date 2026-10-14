import unittest
from types import SimpleNamespace
from app import App


class ChannelMonitorSyncTests(unittest.TestCase):
    def make_app(self, playing=False):
        calls = []
        player = SimpleNamespace(playing=playing, set_enabled_channels=lambda enabled: calls.append(set(enabled)))
        app = App.__new__(App)
        app.player = player
        app.muted_channels = set()
        app.solo_channels = set()
        return app, calls

    def test_muted_channel_is_excluded(self):
        app, calls = self.make_app(True)
        enabled = app.set_channel_monitor_mix({2}, set())
        self.assertNotIn(2, enabled)
        self.assertEqual(calls, [enabled])

    def test_solo_limits_enabled_channels(self):
        app, calls = self.make_app(True)
        self.assertEqual(app.set_channel_monitor_mix(set(), {4, 5}), {4, 5})
        self.assertEqual(calls, [{4, 5}])

    def test_muted_solo_is_still_muted(self):
        app, _ = self.make_app(False)
        self.assertEqual(app.set_channel_monitor_mix({4}, {4, 5}), {5})

    def test_stopped_playback_does_not_send(self):
        app, calls = self.make_app(False)
        app.set_channel_monitor_mix({1}, set())
        self.assertEqual(calls, [])
        self.assertEqual(app.muted_channels, {1})

    def test_rejects_invalid_channels(self):
        app, _ = self.make_app()
        for value in (-1, 16, '1', True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                app.set_channel_monitor_mix({value}, set())
