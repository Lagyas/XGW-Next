import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, MidiError
from playhead_clock import tick_at_seconds, playback_cursor
from transport_ops import elapsed_song_seconds

class TransportClockValidationTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(0, 480, [Track([])])

    def test_infinite_absolute_clock_rejected(self):
        with self.assertRaises(MidiError): tick_at_seconds(self.song, float('inf'))

    def test_boolean_tick_limit_rejected(self):
        with self.assertRaises(MidiError): tick_at_seconds(self.song, 0, True)

    def test_infinite_elapsed_rejected(self):
        with self.assertRaises(MidiError): playback_cursor(self.song, 0, float('inf'))

    def test_nan_elapsed_rejected(self):
        with self.assertRaises(MidiError): playback_cursor(self.song, 0, float('nan'))

    def test_nonfinite_locator_rejected(self):
        with self.assertRaises(MidiError): elapsed_song_seconds(0, 1, 0, float('inf'))

    def test_non_numeric_clock_rejected(self):
        with self.assertRaises(MidiError): elapsed_song_seconds(0, None)

if __name__ == '__main__': unittest.main()
