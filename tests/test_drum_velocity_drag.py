import unittest
from drum_editor import velocity_from_y

class VelocityDragTests(unittest.TestCase):
    def test_bounds(self):
        self.assertEqual(velocity_from_y(-100), 127)
        self.assertEqual(velocity_from_y(999), 1)
    def test_center(self):
        self.assertEqual(velocity_from_y(115-12-(115-32)/2), 64)
    def test_invalid_height(self):
        with self.assertRaises(ValueError):
            velocity_from_y(0, 32)
