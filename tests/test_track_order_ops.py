import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import unittest
from midi import Song, Track, Event, MidiError
from track_order_ops import move_track


class TrackOrderTests(unittest.TestCase):
    def sample(self):
        return Song(1, 480, [Track([Event(0, 0x90 | i, bytes([60+i, 90]))]) for i in range(3)])

    def test_move_preserves_events_and_channel(self):
        song = self.sample()
        before = [t.events[0] for t in song.tracks]
        routes, props = move_track(song, 0, 2)
        self.assertEqual([t.events[0] for t in song.tracks], before[1:] + before[:1])
        self.assertEqual([t.events[0].status for t in song.tracks], [0x91, 0x92, 0x90])
        self.assertEqual((routes, props), ({}, None))
        self.assertTrue(song.dirty)

    def test_routes_follow_tracks(self):
        song = self.sample()
        routes, _ = move_track(song, 2, 0, {0: ('A', None), 2: ('B', 5)})
        self.assertEqual(routes, {1: ('A', None), 0: ('B', 5)})

    def test_xws_properties_follow_tracks(self):
        song = self.sample()
        props = {'source': 'XGworks S4WT', 'tracks': [
            {'track': i, 'channel': i, 'verified': True} for i in range(1, 4)]}
        _, result = move_track(song, 0, 2, xws_properties=props)
        self.assertEqual([row['channel'] for row in result['tracks']], [2, 3, 1])
        self.assertEqual([row['channel'] for row in props['tracks']], [1, 2, 3])

    def test_invalid_position_is_atomic(self):
        song = self.sample()
        original = list(song.tracks)
        with self.assertRaises(MidiError): move_track(song, 0, 3)
        self.assertEqual(song.tracks, original)
        self.assertFalse(song.dirty)

    def test_invalid_route_is_atomic(self):
        song = self.sample()
        original = list(song.tracks)
        with self.assertRaises(MidiError): move_track(song, 0, 2, {1: ('A', 20)})
        self.assertEqual(song.tracks, original)
        self.assertFalse(song.dirty)

    def test_noop_does_not_dirty(self):
        song = self.sample()
        move_track(song, 1, 1)
        self.assertFalse(song.dirty)

if __name__ == '__main__': unittest.main()
