import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event
from app import App

class Player:
    playing = True
    def __init__(self): self.calls = []
    def set_enabled_channels(self, mask): self.calls.append(set(mask))

class ChannelMonitorSharedSafety(unittest.TestCase):
    def make_app(self, shared=True):
        tracks = [Track([Event(0, 0x90, bytes((60, 90)))]),
                  Track([Event(0, 0x90 if shared else 0x91, bytes((62, 90)))])]
        return SimpleNamespace(song=Song(1, 480, tracks), player=Player(),
            muted_tracks={0}, solo_tracks=set(), muted_channels={3}, solo_channels=set())

    def test_conflicting_shared_track_mask_does_not_reach_player(self):
        app = self.make_app()
        with self.assertRaisesRegex(ValueError, 'shared MIDI channel'):
            App.set_channel_monitor_mix(app, {1}, set())
        self.assertEqual(app.player.calls, [])
        self.assertEqual(app.muted_channels, {3})

    def test_disjoint_track_channels_keep_track_mute(self):
        app = self.make_app(False)
        result = App.set_channel_monitor_mix(app, set(), set())
        self.assertEqual(result, {1})
        self.assertEqual(app.player.calls, [{1}])

    def test_stopped_player_can_stage_channel_mix(self):
        app = self.make_app()
        app.player.playing = False
        App.set_channel_monitor_mix(app, {1}, set())
        self.assertEqual(app.muted_channels, {1})
        self.assertEqual(app.player.calls, [])
