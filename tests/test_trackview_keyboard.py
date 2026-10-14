import unittest
from sequencer_view import keyboard_seek_tick
from transport_ops import MAX_TICK


class TrackViewKeyboardTests(unittest.TestCase):
    def test_left_right_beat(self):
        self.assertEqual(keyboard_seek_tick(960, 480, 'Left'), 480)
        self.assertEqual(keyboard_seek_tick(960, 480, 'Right'), 1440)

    def test_shift_fine_step(self):
        self.assertEqual(keyboard_seek_tick(960, 480, 'Left', shift=True), 840)
        self.assertEqual(keyboard_seek_tick(960, 480, 'Right', shift=True), 1080)

    def test_home_end(self):
        self.assertEqual(keyboard_seek_tick(960, 480, 'Home'), 0)
        self.assertEqual(keyboard_seek_tick(960, 480, 'End', 2500), 2500)

    def test_clamps_bounds(self):
        self.assertEqual(keyboard_seek_tick(0, 480, 'Left'), 0)
        self.assertEqual(keyboard_seek_tick(MAX_TICK, 480, 'Right'), MAX_TICK)
        self.assertEqual(keyboard_seek_tick(0, 480, 'End', MAX_TICK + 50), MAX_TICK)

    def test_invalid_division_and_key(self):
        self.assertIsNone(keyboard_seek_tick(0, 0, 'Right'))
        self.assertIsNone(keyboard_seek_tick(0, 0xE728, 'Right'))
        self.assertIsNone(keyboard_seek_tick(0, 480, 'space'))
