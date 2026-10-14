"""Ruler locators should not push each other when dragged across."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import MidiError
from transport_ops import move_locator, MAX_TICK

class LocatorBoundsTests(unittest.TestCase):
    def test_left_moves_inside_region(self):
        self.assertEqual(move_locator('L', 250, 100, 500, 480), (250, 500))

    def test_left_crossing_right_clamps(self):
        self.assertEqual(move_locator('L', 900, 100, 500, 480), (499, 500))

    def test_right_crossing_left_clamps(self):
        self.assertEqual(move_locator('R', 0, 100, 500, 480), (100, 101))

    def test_right_moves_independently(self):
        self.assertEqual(move_locator('R', 800, 100, 500, 480), (100, 800))

    def test_right_at_maximum(self):
        self.assertEqual(move_locator('R', MAX_TICK, 0, 1, 480), (0, MAX_TICK))

    def test_invalid_existing_right_above_midi_limit(self):
        with self.assertRaises(MidiError):
            move_locator('L', 10, 0, MAX_TICK + 1, 480)

    def test_invalid_existing_left_above_midi_limit(self):
        with self.assertRaises(MidiError):
            move_locator('R', 0, MAX_TICK + 1, MAX_TICK + 2, 480)

    def test_invalid_marker(self):
        with self.assertRaises(MidiError):
            move_locator('X', 250, 100, 500, 480)

    def test_invalid_initial_region(self):
        with self.assertRaises(MidiError):
            move_locator('L', 100, 500, 100, 480)

    def test_negative_target_rejected(self):
        with self.assertRaises(MidiError):
            move_locator('R', -1, 100, 500, 480)
