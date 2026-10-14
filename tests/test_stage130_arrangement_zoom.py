import unittest
from sequencer_view import zoom_row_height, ROW_HEIGHT


class ArrangementZoomTests(unittest.TestCase):
    def test_vertical_zoom_in_and_out(self):
        self.assertGreater(zoom_row_height(ROW_HEIGHT, 1), ROW_HEIGHT)
        self.assertLess(zoom_row_height(ROW_HEIGHT, -1), ROW_HEIGHT)

    def test_vertical_zoom_limits(self):
        self.assertEqual(zoom_row_height(42, 100), 168)
        self.assertEqual(zoom_row_height(42, -100), 24)

    def test_invalid_vertical_zoom(self):
        with self.assertRaises(ValueError):
            zoom_row_height(0, 1)
