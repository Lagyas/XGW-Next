import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Event, Track, Song, MidiError
from note_ops import quantize_selected_notes

def song_with_notes():
    return Song(0, 480, [Track([
        Event(65, 0x90, bytes((60, 100)), order=0),
        Event(185, 0x80, bytes((60, 0)), order=1),
        Event(190, 0x90, bytes((64, 90)), order=2),
        Event(310, 0x80, bytes((64, 0)), order=3),
        Event(310, 0xff, b"", 0x2f, 4),
    ])])

class SelectedQuantizeTests(unittest.TestCase):
    def test_only_selected_note_moves(self):
        song = song_with_notes()
        count = quantize_selected_notes(song, 0, [(0, 1)], 16)
        self.assertEqual(count, 1)
        self.assertEqual(song.tracks[0].events[0].tick, 120)
        self.assertEqual(song.tracks[0].events[1].tick, 240)
        self.assertEqual(song.tracks[0].events[2].tick, 190)
        self.assertEqual(song.tracks[0].events[3].tick, 310)

    def test_multiple_notes_and_roundtrip(self):
        song = song_with_notes()
        quantize_selected_notes(song, 0, [(0, 1), (2, 3)], 16)
        restored = Song.from_bytes(song.to_bytes())
        notes = [(e.tick, e.data[0]) for e in restored.tracks[0].events
                 if e.status & 0xf0 == 0x90]
        self.assertEqual(notes, [(120, 60), (240, 64)])

    def test_invalid_selection_is_atomic(self):
        song = song_with_notes()
        before = [e.tick for e in song.tracks[0].events]
        with self.assertRaises(MidiError):
            quantize_selected_notes(song, 0, [(0, 1), (1, 2)], 16)
        self.assertEqual([e.tick for e in song.tracks[0].events], before)

    def test_strength_zero_does_not_dirty(self):
        song = song_with_notes()
        song.dirty = False
        self.assertEqual(quantize_selected_notes(song, 0, [(0, 1)], 16, 0), 0)
        self.assertFalse(song.dirty)

if __name__ == "__main__":
    unittest.main()
