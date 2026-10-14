import unittest
from sequencer_view import locator_hit_test, LEFT_WIDTH, BEAT_WIDTH, HEADER_HEIGHT

class LocatorDragTests(unittest.TestCase):
    def test_left_and_right_handles(self):
        self.assertEqual(locator_hit_test(LEFT_WIDTH, 10, 480, 0, 1920), "L")
        self.assertEqual(locator_hit_test(LEFT_WIDTH + 4 * BEAT_WIDTH, 10, 480, 0, 1920), "R")

    def test_miss_and_track_area(self):
        self.assertIsNone(locator_hit_test(LEFT_WIDTH + 40, 10, 480, 0, 1920))
        self.assertIsNone(locator_hit_test(LEFT_WIDTH, HEADER_HEIGHT, 480, 0, 1920))

    def test_invalid_division(self):
        self.assertIsNone(locator_hit_test(LEFT_WIDTH, 10, 0, 0, 1920))
        self.assertIsNone(locator_hit_test(LEFT_WIDTH, 10, 0xE728, 0, 1920))
