"""Regression tests for invalid and boundary loop-clock inputs."""
import math
import unittest

from midi import MidiError
from transport_ops import elapsed_song_seconds, move_locator, MAX_TICK


class Stage122LoopClockTests(unittest.TestCase):
    def test_partial_first_leg_then_wrap(self):
        self.assertEqual(elapsed_song_seconds(2, 2, 4, 10), 4)
        self.assertEqual(elapsed_song_seconds(2, 8, 4, 10), 4)
        self.assertEqual(elapsed_song_seconds(2, 9.5, 4, 10), 5.5)

    def test_invalid_locator_values_raise_midi_error(self):
        for left, right in [('bad', 10), (4, 'bad'),
                            (math.inf, 10), (4, math.nan), (10, 4), (4, 4)]:
            with self.subTest(left=left, right=right), self.assertRaises(MidiError):
                elapsed_song_seconds(2, 1, left, right)

    def test_incomplete_loop_disables_loop(self):
        self.assertEqual(elapsed_song_seconds(2, 3, None, 10), 5)
        self.assertEqual(elapsed_song_seconds(2, 3, 4, None), 5)

    def test_invalid_elapsed_and_start(self):
        for elapsed, start in [(math.inf, 2), (0, math.nan), ('oops', 2)]:
            with self.subTest(elapsed=elapsed, start=start), self.assertRaises(MidiError):
                elapsed_song_seconds(start, elapsed, 4, 10)

    def test_drag_locators_clamps_without_crossing(self):
        self.assertEqual(move_locator('L', 100, 10, 50, 480), (49, 50))
        self.assertEqual(move_locator('R', 0, 10, 50, 480), (10, 11))
        self.assertEqual(move_locator('R', MAX_TICK, 10, 50, 480), (10, MAX_TICK))


if __name__ == '__main__':
    unittest.main()
