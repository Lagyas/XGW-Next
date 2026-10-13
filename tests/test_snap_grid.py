import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import MidiError
from snap_grid import SNAP_OPTIONS, snap_ticks, snapped_tick

class SnapGridTests(unittest.TestCase):
    def test_standard_ppqn(self):
        self.assertEqual(snap_ticks(480, "1/4"), 480)
        self.assertEqual(snap_ticks(480, "1/8"), 240)
        self.assertEqual(snap_ticks(480, "1/16"), 120)
        self.assertEqual(snap_ticks(480, "1/32"), 60)
        self.assertEqual(snap_ticks(480, "1/64"), 30)

    def test_snap_to_nearest(self):
        self.assertEqual(snapped_tick(178, 480, "1/16"), 120)
        self.assertEqual(snapped_tick(181, 480, "1/16"), 240)
        self.assertEqual(snapped_tick(0, 480, "1/8"), 0)

    def test_off_preserves_original_tick(self):
        self.assertEqual(snapped_tick(173, 480, "Off"), 173)

    def test_reject_unknown_or_invalid_timing(self):
        with self.assertRaises(MidiError):
            snap_ticks(480, "1/3")
        with self.assertRaises(MidiError):
            snap_ticks(0xe728, "1/16")
        with self.assertRaises(MidiError):
            snap_ticks(10, "1/64")
        with self.assertRaises(MidiError):
            snapped_tick(-1, 480, "1/16")

    def test_snap_options(self):
        self.assertEqual(SNAP_OPTIONS, ("Off", "1/4", "1/8", "1/16", "1/32", "1/64"))

if __name__ == "__main__":
    unittest.main()
