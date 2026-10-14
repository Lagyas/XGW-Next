import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from transport_ops import elapsed_song_seconds
from midi import MidiError

class TransportClockTests(unittest.TestCase):
    def test_plain_playback(self):
        self.assertEqual(elapsed_song_seconds(10, 4), 14)
    def test_initial_cursor_not_left_locator(self):
        self.assertEqual(elapsed_song_seconds(15, 2, 10, 20), 17)
    def test_wrap_exactly_at_right(self):
        self.assertEqual(elapsed_song_seconds(15, 5, 10, 20), 10)
    def test_wrap_repeatedly(self):
        self.assertEqual(elapsed_song_seconds(15, 27, 10, 20), 12)
    def test_negative_elapsed_clamped(self):
        self.assertEqual(elapsed_song_seconds(15, -2, 10, 20), 15)
    def test_invalid_region(self):
        with self.assertRaises(MidiError):
            elapsed_song_seconds(10, 2, 20, 20)
    def test_cursor_before_left_allowed(self):
        self.assertEqual(elapsed_song_seconds(5, 16, 10, 20), 11)

if __name__ == '__main__':
    unittest.main()
