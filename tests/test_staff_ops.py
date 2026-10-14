import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import MidiError, Event, Track
from staff_ops import staff_position, staff_notes

class StaffTests(unittest.TestCase):
    def test_treble_bottom_line_e4(self):
        self.assertEqual(staff_position(64, "treble"), (0, False))

    def test_bass_bottom_line_g2(self):
        self.assertEqual(staff_position(43, "bass"), (0, False))

    def test_middle_c_ledger_below_treble(self):
        self.assertEqual(staff_position(60, "treble"), (-2, False))

    def test_f_sharp(self):
        self.assertEqual(staff_position(66, "treble"), (1, True))

    def test_invalid_pitch_and_clef(self):
        for pitch in (-1, 128, True, 64.0):
            with self.assertRaises(MidiError):
                staff_position(pitch)
        with self.assertRaises(MidiError):
            staff_position(60, "alto")

    def test_note_pairing_and_channel_filter(self):
        track = Track([Event(0, 0x90, bytes((60, 100))),
                       Event(120, 0x80, bytes((60, 0))),
                       Event(10, 0x91, bytes((64, 80))),
                       Event(240, 0x81, bytes((64, 0)))])
        self.assertEqual(len(staff_notes(track)), 2)
        self.assertEqual(staff_notes(track, 1), [(10, 240, 64, 80, 1)])
        self.assertEqual(staff_notes(track, 0), [(0, 120, 60, 100, 0)])

    def test_invalid_channel(self):
        for ch in (-1, 16, True):
            with self.assertRaises(MidiError):
                staff_notes(Track(), ch)

class StaffRestsTests(unittest.TestCase):
    def test_gap_before_and_between_notes(self):
        from staff_ops import staff_rest_spans
        notes = [(120, 240, 60, 100, 0), (360, 480, 64, 100, 0)]
        self.assertEqual(staff_rest_spans(notes, 480), [(0, 120), (240, 360)])

    def test_overlapping_chord_does_not_create_false_rest(self):
        from staff_ops import staff_rest_spans
        notes = [(0, 480, 60, 100, 0), (120, 240, 64, 100, 0),
                 (600, 720, 67, 100, 0)]
        self.assertEqual(staff_rest_spans(notes, 480), [(480, 600)])

    def test_trailing_rest_is_optional(self):
        from staff_ops import staff_rest_spans
        self.assertEqual(staff_rest_spans([(0, 120, 60, 80, 0)], 480), [])
        self.assertEqual(staff_rest_spans([(0, 120, 60, 80, 0)], 480, 480),
                         [(120, 480)])

    def test_rest_validation(self):
        from staff_ops import staff_rest_spans
        for notes, division, end in (([], 0, None), ([], True, None),
                                     ([(5, 4, 60, 80, 0)], 480, None),
                                     ([], 480, -1)):
            with self.assertRaises(MidiError):
                staff_rest_spans(notes, division, end)
