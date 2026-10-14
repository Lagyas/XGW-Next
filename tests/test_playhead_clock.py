import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from playhead_clock import playback_cursor, tick_at_seconds


class PlayheadClockTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(0, 480, [Track([])])

    def test_cursor_at_start(self):
        self.assertEqual(playback_cursor(self.song, 480, 0), 480)

    def test_cursor_advances(self):
        self.assertEqual(playback_cursor(self.song, 480, 0.5), 960)

    def test_first_partial_loop(self):
        self.assertEqual(playback_cursor(self.song, 960, 0.25, 480, 1920), 1200)

    def test_loop_exact_right_wraps(self):
        self.assertEqual(playback_cursor(self.song, 960, 1.0, 480, 1920), 480)

    def test_loop_repeats(self):
        self.assertEqual(playback_cursor(self.song, 960, 2.0, 480, 1920), 1440)

    def test_before_left_first_pass(self):
        self.assertEqual(playback_cursor(self.song, 0, 0.25, 480, 1920), 240)

    def test_fractional_tick_floors(self):
        self.assertEqual(tick_at_seconds(self.song, 0.0015), 1)

    def test_maximum_bound(self):
        self.assertEqual(tick_at_seconds(self.song, 100, 500), 500)

    def test_negative_clock_rejected(self):
        with self.assertRaises(MidiError):
            tick_at_seconds(self.song, -1)

    def test_nan_clock_rejected(self):
        with self.assertRaises(MidiError):
            tick_at_seconds(self.song, float('nan'))


if __name__ == '__main__':
    unittest.main()
