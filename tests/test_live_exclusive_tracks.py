import unittest
from midi import Song, Track, Event
from track_channels import audible_channels

class ExclusiveTrackMixTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [
            Track([Event(0, 0x90, bytes([60, 100]), 0)]),
            Track([Event(0, 0x91, bytes([64, 100]), 0)])])

    def test_all_tracks(self):
        self.assertEqual(audible_channels(self.song), {0, 1})

    def test_mute_track(self):
        self.assertEqual(audible_channels(self.song, muted_tracks={0}), {1})

    def test_solo_track(self):
        self.assertEqual(audible_channels(self.song, solo_tracks={1}), {1})

    def test_channel_mute_combined_with_track_solo(self):
        self.assertEqual(audible_channels(self.song, solo_tracks={1}, muted_channels={1}), set())

    def test_shared_channel_requires_conflicting_track_mask(self):
        self.song.tracks[1].events[0].status = 0x90
        with self.assertRaises(ValueError):
            audible_channels(self.song, muted_tracks={0})
