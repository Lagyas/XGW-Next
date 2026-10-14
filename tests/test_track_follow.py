"""Track View horizontal cursor-follow behavior without a GUI display."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from sequencer_view import follow_scroll_fraction


class FollowTests(unittest.TestCase):
    def test_visible_cursor_does_not_scroll(self):
        self.assertIsNone(follow_scroll_fraction(500, 200, 800, 2400))

    def test_cursor_at_far_right_scrolls(self):
        self.assertAlmostEqual(follow_scroll_fraction(1400, 200, 800, 2400), 0.65)

    def test_cursor_behind_fixed_column_scrolls_back(self):
        self.assertEqual(follow_scroll_fraction(250, 400, 800, 2400), 0)

    def test_no_scroll_for_short_song(self):
        self.assertIsNone(follow_scroll_fraction(500, 0, 800, 600))

    def test_zero_viewport_is_safe(self):
        self.assertIsNone(follow_scroll_fraction(500, 0, 0, 2000))

    def test_scroll_is_clamped_at_end(self):
        self.assertEqual(follow_scroll_fraction(5000, 0, 800, 2000), 1)


if __name__ == "__main__":
    unittest.main()
