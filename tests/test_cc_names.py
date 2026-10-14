import unittest
from cc_names import cc_label


class CCNamesTests(unittest.TestCase):
    def test_common_controllers(self):
        self.assertEqual(cc_label(7), "CC 007 – Channel Volume MSB")
        self.assertEqual(cc_label(10), "CC 010 – Pan MSB")
        self.assertEqual(cc_label(64), "CC 064 – Damper Pedal (Sustain)")
        self.assertEqual(cc_label(91), "CC 091 – Effects 1 Depth (Reverb Send)")
        self.assertEqual(cc_label(93), "CC 093 – Effects 3 Depth (Chorus Send)")

    def test_unknown_controllers_still_selectable(self):
        self.assertEqual(cc_label(3), "CC 003 – Undefined / device-specific")
        self.assertEqual(cc_label(119), "CC 119 – Undefined / device-specific")

    def test_full_midi_range(self):
        for number in range(128):
            self.assertTrue(cc_label(number).startswith(f"CC {number:03d} – "))

    def test_invalid_numbers(self):
        for number in (-1, 128, 1.5, True, None, "7"):
            with self.assertRaises(ValueError):
                cc_label(number)
