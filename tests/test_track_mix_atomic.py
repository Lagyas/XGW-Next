import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from app import App
from midi import Song, Track, Event

class Player:
    def __init__(self, playing=True, fail=False):
        self.playing, self.fail, self.last = playing, fail, None
    def set_enabled_channels(self, channels):
        if self.fail:
            raise RuntimeError('MIDI output failed')
        self.last = set(channels)

class Sequencer:
    def __init__(self):
        self.calls = []
    def set_mix(self, muted, solo):
        self.calls.append((set(muted), set(solo)))

class TrackMixAtomicTests(unittest.TestCase):
    def app(self, playing=True, fail=False):
        song = Song(1, 480, [Track([Event(0, 0x90, bytes([60, 100]), 0)]),
                             Track([Event(0, 0x91, bytes([62, 100]), 0)])])
        return SimpleNamespace(song=song, player=Player(playing, fail),
            sequencer=Sequencer(), muted_tracks=set(), solo_tracks=set(),
            muted_channels=set(), solo_channels=set())

    def test_live_failure_does_not_publish_track_state(self):
        app = self.app(fail=True)
        with self.assertRaises(RuntimeError):
            App.toggle_track_state(app, 0, 'mute')
        self.assertEqual(app.muted_tracks, set())
        self.assertEqual(app.sequencer.calls, [])

    def test_live_success_publishes_both(self):
        app = self.app()
        App.toggle_track_state(app, 0, 'mute')
        self.assertEqual(app.player.last, {1})
        self.assertEqual(app.muted_tracks, {0})
        self.assertEqual(app.sequencer.calls, [({0}, set())])

    def test_stopped_changes_state_without_player_call(self):
        app = self.app(playing=False)
        App.toggle_track_state(app, 1, 'solo')
        self.assertEqual(app.solo_tracks, {1})
        self.assertIsNone(app.player.last)

    def test_invalid_control_does_not_change_state(self):
        app = self.app()
        with self.assertRaises(ValueError):
            App.toggle_track_state(app, 0, 'other')
        self.assertEqual(app.sequencer.calls, [])

if __name__ == '__main__':
    unittest.main()
