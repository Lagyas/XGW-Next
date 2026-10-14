import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event
from track_channels import track_channels, shared_channels, unsafe_live_track_changes


class TrackChannelsTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [
            Track([Event(0, 0xff, b'X', 3, 0)]),
            Track([Event(0, 0x90, b'\x3c\x64', order=0), Event(1, 0xb2, b'\x07\x40', order=1)]),
            Track([Event(0, 0x80, b'\x3c\x00', order=0)]),
            Track([Event(0, 0x93, b'\x40\x64', order=0)]),
        ])

    def test_channel_ownership(self):
        self.assertEqual(track_channels(self.song), {0: frozenset(), 1: frozenset({0, 2}),
                                                     2: frozenset({0}), 3: frozenset({3})})

    def test_shared_channels(self):
        self.assertEqual(shared_channels(self.song), {0: frozenset({1, 2})})

    def test_unsafe_tracks(self):
        self.assertEqual(unsafe_live_track_changes(self.song, {1, 2, 3}),
                         {1: frozenset({0}), 2: frozenset({0})})

    def test_empty_song(self):
        self.assertEqual(shared_channels(Song(0, 480, [])), {})
