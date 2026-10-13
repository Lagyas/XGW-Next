import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Event, Track, Song, MidiError
from meter_grid import meter_changes, grid_lines

def song(*signatures):
    events = [Event(tick, 0xff, bytes((num, exponent, 24, 8)), 0x58, i)
              for i, (tick, num, exponent) in enumerate(signatures)]
    events.append(Event(max([x[0] for x in signatures], default=0),
                        0xff, b"", 0x2f, 20))
    return Song(1, 480, [Track(events)])

class MeterGridTests(unittest.TestCase):
    def test_default_four_four(self):
        marks = grid_lines(song(), 3840)
        bars = [(tick, number) for tick, is_bar, number in marks if is_bar]
        self.assertEqual(bars[:3], [(0, 1), (1920, 2), (3840, 3)])

    def test_three_four(self):
        marks = grid_lines(song((0, 3, 2)), 4320)
        bars = [tick for tick, is_bar, _ in marks if is_bar]
        self.assertEqual(bars[:4], [0, 1440, 2880, 4320])

    def test_six_eight(self):
        marks = grid_lines(song((0, 6, 3)), 2880)
        bars = [tick for tick, is_bar, _ in marks if is_bar]
        self.assertEqual(bars[:3], [0, 1440, 2880])
        self.assertIn((240, False, 1), marks)

    def test_change_mid_bar_starts_new_bar(self):
        marks = grid_lines(song((0, 4, 2), (960, 3, 2)), 3840)
        bars = [(tick, number) for tick, is_bar, number in marks if is_bar]
        self.assertEqual(bars[:3], [(0, 1), (960, 2), (2400, 3)])

    def test_change_on_bar_boundary(self):
        marks = grid_lines(song((0, 4, 2), (1920, 3, 2)), 4800)
        bars = [(tick, number) for tick, is_bar, number in marks if is_bar]
        self.assertEqual(bars[:4], [(0, 1), (1920, 2), (3360, 3), (4800, 4)])

    def test_last_signature_at_same_tick_wins(self):
        self.assertEqual(meter_changes(song((0, 4, 2), (0, 7, 3))), [(0, 7, 8)])

    def test_reject_smpte(self):
        smpte = Song(0, 0xe728, [Track([])])
        with self.assertRaises(MidiError):
            grid_lines(smpte, 1000)

if __name__ == "__main__":
    unittest.main()
