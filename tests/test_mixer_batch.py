import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from mixer_ops import set_mixer_batch, channel_values

class MixerBatchTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [Track([Event(0, 0xff, b'', 0x2f, 0)])])

    def test_multiple_channels(self):
        self.assertEqual(set_mixer_batch(self.song, 0, {1: {'Volume': 42}, 16: {'Variation': 77}}, 120), 2)
        self.assertEqual(channel_values(self.song, 1, 120)['Volume'], 42)
        self.assertEqual(channel_values(self.song, 16, 120)['Variation'], 77)

    def test_invalid_later_channel_does_not_partially_write(self):
        before = self.song.to_bytes()
        with self.assertRaises(MidiError):
            set_mixer_batch(self.song, 0, {1: {'Volume': 42}, 17: {'Pan': 64}}, 120)
        self.assertEqual(self.song.to_bytes(), before)

    def test_invalid_later_value_does_not_partially_write(self):
        before = self.song.to_bytes()
        with self.assertRaises(MidiError):
            set_mixer_batch(self.song, 0, {1: {'Volume': 42}, 2: {'Pan': 200}}, 120)
        self.assertEqual(self.song.to_bytes(), before)

    def test_empty_batch_no_change(self):
        before = self.song.to_bytes()
        self.assertEqual(set_mixer_batch(self.song, 0, {}, 120), 0)
        self.assertEqual(self.song.to_bytes(), before)

    def test_invalid_tick_no_change(self):
        before = self.song.to_bytes()
        with self.assertRaises(MidiError):
            set_mixer_batch(self.song, 0, {1: {'Volume': 42}}, -1)
        self.assertEqual(self.song.to_bytes(), before)
