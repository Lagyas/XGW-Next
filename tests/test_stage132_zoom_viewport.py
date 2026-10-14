import unittest
from sequencer_view import HEADER_HEIGHT, vertical_zoom_fraction


class VerticalZoomViewportTests(unittest.TestCase):
    def test_keeps_visible_track_and_fraction(self):
        old, new = 42, 84
        top = HEADER_HEIGHT + 7.5 * old
        content = HEADER_HEIGHT + 30 * new
        fraction = vertical_zoom_fraction(top, old, new, content, 450)
        self.assertAlmostEqual(fraction * content, HEADER_HEIGHT + 7.5 * new)

    def test_clamps_near_end(self):
        self.assertAlmostEqual(vertical_zoom_fraction(5000, 42, 84, 1000, 300), .7)

    def test_short_content(self):
        self.assertEqual(vertical_zoom_fraction(500, 42, 84, 100, 300), 0)

    def test_invalid_height(self):
        self.assertEqual(vertical_zoom_fraction(200, 0, 84, 1000, 300), 0)
