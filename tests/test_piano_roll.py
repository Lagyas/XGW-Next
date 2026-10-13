import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Event, Track
from piano_roll import extract_notes, pitch_label

class PianoRollTests(unittest.TestCase):
    def test_note_on_velocity_zero_is_note_off(self):
        track = Track([
            Event(0, 0x90, bytes([60, 100]), order=0),
            Event(240, 0x90, bytes([60, 0]), order=1)
        ])
        self.assertEqual(extract_notes(track), [(0, 240, 60, 1, 100, 0, 1)])

    def test_channels_separate(self):
        track = Track([
            Event(0, 0x90, bytes([60, 100]), order=0),
            Event(0, 0x91, bytes([60, 80]), order=1),
            Event(120, 0x81, bytes([60, 0]), order=2),
            Event(240, 0x80, bytes([60, 0]), order=3),
        ])
        notes = extract_notes(track)
        self.assertEqual([(n[1], n[3]) for n in notes], [(240, 1), (120, 2)])

    def test_orphaned_note_on_ignored(self):
        self.assertEqual(extract_notes(Track([Event(0, 0x90, bytes([60, 100]))])), [])

    def test_pitch_label(self):
        self.assertEqual(pitch_label(60), "C4")
        self.assertEqual(pitch_label(69), "A4")

if __name__ == "__main__":
    unittest.main()
