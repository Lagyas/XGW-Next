import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))

from midi import Event, Track, Song, MidiError
from note_ops import paired_notes, insert_note, delete_note, move_note, quantize_notes

def song():
    return Song(0, 480, [Track([
        Event(0, 0x90, bytes((60, 100)), order=0),
        Event(120, 0x80, bytes((60, 0)), order=1),
        Event(120, 0xff, b"", 0x2f, 2),
    ])])

class NoteOpsTests(unittest.TestCase):
    def test_insert_roundtrip_and_end_of_track(self):
        s = song()
        insert_note(s, 0, 480, 240, 64, channel=2)
        t = Song.from_bytes(s.to_bytes())
        self.assertEqual(len(paired_notes(t.tracks[0])), 2)
        endings = [e for e in t.tracks[0].events if e.status == 0xff and e.meta_type == 0x2f]
        self.assertEqual(len(endings), 1)
        self.assertEqual(endings[0].tick, 720)

    def test_move_note(self):
        s = song()
        move_note(s, 0, 0, 1, 240, 65)
        t = Song.from_bytes(s.to_bytes())
        pairs = paired_notes(t.tracks[0])
        self.assertEqual(len(pairs), 1)
        on_idx, off_idx = pairs[0]
        self.assertEqual(t.tracks[0].events[on_idx].data[0], 65)
        self.assertEqual(t.tracks[0].events[on_idx].tick, 240)
        self.assertEqual(t.tracks[0].events[off_idx].tick, 360)

    def test_delete_note(self):
        s = song()
        delete_note(s, 0, 0, 1)
        self.assertEqual(len(s.tracks[0].events), 1)
        self.assertEqual(len(paired_notes(s.tracks[0])), 0)

    def test_quantize_preserves_duration(self):
        s = song()
        s.tracks[0].events[0].tick = 70
        s.tracks[0].events[1].tick = 190
        count = quantize_notes(s, 0, denominator=16)
        self.assertEqual(count, 1)
        self.assertEqual(s.tracks[0].events[0].tick, 120)
        self.assertEqual(s.tracks[0].events[1].tick, 240)

    def test_invalid_insert_does_not_mutate(self):
        s = song()
        with self.assertRaises(MidiError):
            insert_note(s, 0, 0, 120, 128)
        self.assertEqual(len(s.tracks[0].events), 3)

if __name__ == "__main__":
    unittest.main()
