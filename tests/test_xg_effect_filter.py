import unittest
from xg_effect_filter import EFFECT_FILTERS, filter_effect_rows


class XGEffectFilterTests(unittest.TestCase):
    def setUp(self):
        self.rows = [(0, 0, "reverb", (2, 1, 0), b"\x01\x00"),
                     (0, 0, "variation", (2, 1, 64), b"\x00\x00"),
                     (0, 0, "chorus", (2, 1, 32), b"\x41\x00"),
                     (1, 0, "reverb", (2, 1, 1), b"\x20")]

    def test_all_preserves_order(self):
        self.assertEqual(filter_effect_rows(self.rows), self.rows)

    def test_each_effect(self):
        for effect in EFFECT_FILTERS[1:]:
            self.assertEqual(filter_effect_rows(self.rows, effect),
                             [r for r in self.rows if r[2] == effect.lower()])

    def test_unknown_filter_rejected(self):
        with self.assertRaises(ValueError):
            filter_effect_rows(self.rows, "Insertion")

    def test_does_not_mutate_rows(self):
        original = self.rows[:]
        filter_effect_rows(self.rows, "Chorus")
        self.assertEqual(self.rows, original)
