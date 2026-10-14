import unittest
from midi import MidiError
from track_order_ops import remap_track_indices


class TrackMixRemapTests(unittest.TestCase):
    def test_move_forward_shifts_intermediate_flags(self):
        self.assertEqual(remap_track_indices({0, 1, 3}, 0, 3, 5), {0, 2, 3})

    def test_move_backward_shifts_intermediate_flags(self):
        self.assertEqual(remap_track_indices({0, 2, 4}, 4, 1, 5), {0, 1, 3})

    def test_same_position(self):
        self.assertEqual(remap_track_indices({0, 2}, 2, 2, 4), {0, 2})

    def test_invalid_position(self):
        with self.assertRaises(MidiError):
            remap_track_indices({0}, -1, 2, 4)
