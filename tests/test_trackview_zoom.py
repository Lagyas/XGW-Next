import unittest
from sequencer_view import zoom_beat_width, zoom_scroll_fraction, locator_hit_test, LEFT_WIDTH


class TimelineZoomTests(unittest.TestCase):
    def test_zoom_in(self):
        self.assertEqual(zoom_beat_width(28, 1), 35)

    def test_zoom_out(self):
        self.assertEqual(zoom_beat_width(40, -1), 32)

    def test_zoom_limits(self):
        self.assertEqual(zoom_beat_width(28, 100), 224)
        self.assertEqual(zoom_beat_width(28, -100), 8)

    def test_zoom_invalid(self):
        for value in (0, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                zoom_beat_width(value, 1)

    def test_pointer_anchor(self):
        # tick 960 (two beats at 480 PPQ) remains at screen x=150
        self.assertAlmostEqual(zoom_scroll_fraction(960, 480, 40, 150, 500, 1500), 160 / 1500)

    def test_locator_hit_zoom(self):
        self.assertEqual(locator_hit_test(LEFT_WIDTH + 80, 10, 480, 960, 1920, beat_width=40), 'L')
        self.assertIsNone(locator_hit_test(LEFT_WIDTH + 80, 10, 480, 960, 4000, beat_width=20))
