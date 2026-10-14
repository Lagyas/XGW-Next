import unittest
from drum_editor import drum_insert_tick
from midi import MidiError

class DrumSnapTests(unittest.TestCase):
    def test_sixteenth(self):
        self.assertEqual(drum_insert_tick(119, 480, '1/16'), 120)
    def test_eighth(self):
        self.assertEqual(drum_insert_tick(119, 480, '1/8'), 0)
    def test_off(self):
        self.assertEqual(drum_insert_tick(119, 480, 'Off'), 119)
    def test_invalid_grid(self):
        with self.assertRaises(MidiError):
            drum_insert_tick(12, 480, 'invalid')
    def test_invalid_position(self):
        with self.assertRaises(MidiError):
            drum_insert_tick(-1, 480)
