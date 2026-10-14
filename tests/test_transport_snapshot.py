import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, MidiError
from transport_snapshot import cursor_snapshot

class TransportSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(0, 480, [Track([])])

    def test_absent_clock(self):
        self.assertIsNone(cursor_snapshot(self.song, None, 12))

    def test_stop_between_ui_frames(self):
        self.assertEqual(cursor_snapshot(self.song, (10, 480, None, None), 10.25), 720)

    def test_early_clock_clamped(self):
        self.assertEqual(cursor_snapshot(self.song, (10, 480, None, None), 9.5), 480)

    def test_stop_on_loop_boundary(self):
        self.assertEqual(cursor_snapshot(self.song, (10, 960, 480, 1920), 11), 480)

    def test_loop_inside(self):
        self.assertEqual(cursor_snapshot(self.song, (10, 960, 480, 1920), 10.5), 1440)

    def test_nan_timestamp(self):
        with self.assertRaises(MidiError):
            cursor_snapshot(self.song, (10, 0, None, None), float('nan'))

if __name__ == '__main__':
    unittest.main()
