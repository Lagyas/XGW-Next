import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, MidiError
from midi_output import timed_messages, chase_messages, loop_messages, validate_enabled_channels


class PlaybackChannelMaskTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [Track([])])

    def test_timeline_rejects_bad_channel_masks(self):
        for mask in ({16}, {-1}, {True}, {'1'}, 4):
            with self.subTest(mask=mask), self.assertRaises(MidiError):
                list(timed_messages(self.song, enabled_channels=mask))

    def test_chase_rejects_bad_masks_even_at_tick_zero(self):
        with self.assertRaises(MidiError):
            chase_messages(self.song, 0, enabled_channels={16})

    def test_loop_rejects_bad_masks(self):
        with self.assertRaises(MidiError):
            loop_messages(self.song, 0, 480, enabled_channels={16})

    def test_valid_masks_are_not_modified(self):
        original = {0, 9, 15}
        self.assertEqual(validate_enabled_channels(original), original)
        self.assertEqual(list(timed_messages(self.song, enabled_channels=original)), [])
        self.assertEqual(original, {0, 9, 15})
