import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event
from track_channels import audible_channels


class SharedChannelMasks(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [
            Track([Event(0, 0x90, b'\x3c\x40')]),
            Track([Event(0, 0x90, b'\x40\x40')]),
            Track([Event(0, 0x91, b'\x41\x40')]),
        ])

    def test_shared_channel_all_active(self):
        self.assertEqual(audible_channels(self.song), {0, 1})

    def test_shared_channel_both_muted(self):
        self.assertEqual(audible_channels(self.song, muted_tracks={0, 1}), {1})

    def test_shared_channel_conflicting_mute(self):
        with self.assertRaises(ValueError):
            audible_channels(self.song, muted_tracks={0})

    def test_shared_channel_conflicting_solo(self):
        with self.assertRaises(ValueError):
            audible_channels(self.song, solo_tracks={0})

    def test_channel_mask_still_applies(self):
        self.assertEqual(audible_channels(self.song, muted_channels={1}), {0})
