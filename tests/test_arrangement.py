import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Event, Track
from arrangement import track_clips

def note(tick, end, pitch=60, channel=0):
    return [
        Event(tick, 0x90 | channel, bytes((pitch, 100)), order=tick),
        Event(end, 0x80 | channel, bytes((pitch, 0)), order=end),
    ]

class ArrangementTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(track_clips(Track([]), 480), [])

    def test_gap_creates_two_clips(self):
        events = note(0, 480) + note(2400, 2880)
        self.assertEqual(track_clips(Track(events), 480), [(0, 480), (2400, 2880)])

    def test_overlapping_notes_merge(self):
        events = note(0, 960, 60) + note(480, 1440, 62)
        self.assertEqual(track_clips(Track(events), 480), [(0, 1440)])

    def test_short_gap_stays_in_same_clip(self):
        events = note(0, 240) + note(1200, 1440)
        self.assertEqual(track_clips(Track(events), 480), [(0, 1440)])

    def test_smpte_unsupported(self):
        self.assertEqual(track_clips(Track(note(0, 480)), 0xe728), [])

if __name__ == "__main__":
    unittest.main()
