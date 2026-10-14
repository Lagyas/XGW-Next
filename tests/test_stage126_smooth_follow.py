import unittest
from sequencer_view import smooth_follow_fraction

class SmoothFollowTests(unittest.TestCase):
    def test_anchor(self):
        self.assertAlmostEqual(smooth_follow_fraction(1000, 0, 800, 2400), (1000-(230+570*.4))/1600)
    def test_start(self):
        self.assertIsNone(smooth_follow_fraction(100, 0, 800, 2400))
    def test_end(self):
        self.assertEqual(smooth_follow_fraction(9000, 0, 800, 2400), 1)
    def test_too_narrow(self):
        self.assertIsNone(smooth_follow_fraction(500, 0, 200, 2400))
