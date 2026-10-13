import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Event, Track, Song, MidiError
from note_ops import edit_note_event, delete_note_event

def example():
    return Song(0, 480, [Track([
        Event(120, 0x90, bytes((60, 100)), order=0),
        Event(360, 0x80, bytes((60, 0)), order=1),
        Event(400, 0xff, b"", 0x2f, 2),
    ])])

class PairedNoteEditingTests(unittest.TestCase):
    def test_change_note_on_pitch_updates_note_off(self):
        song = example()
        self.assertTrue(edit_note_event(song, 0, 0, 150, bytes((65, 70))))
        on, off = song.tracks[0].events[:2]
        self.assertEqual((on.tick, on.data), (150, bytes((65, 70))))
        self.assertEqual((off.tick, off.data), (360, bytes((65, 0))))
        self.assertEqual(Song.from_bytes(song.to_bytes()).tracks[0].events[1].data[0], 65)

    def test_change_note_off_pitch_updates_note_on(self):
        song = example()
        edit_note_event(song, 0, 1, 480, bytes((67, 0)))
        on, off = song.tracks[0].events[:2]
        self.assertEqual(on.data, bytes((67, 100)))
        self.assertEqual((off.tick, off.data), (480, bytes((67, 0))))

    def test_invalid_end_before_start_does_not_mutate(self):
        song = example()
        before = [(e.tick, e.data) for e in song.tracks[0].events]
        with self.assertRaises(MidiError):
            edit_note_event(song, 0, 1, 100, bytes((64, 0)))
        self.assertEqual([(e.tick, e.data) for e in song.tracks[0].events], before)

    def test_reject_note_on_zero_velocity(self):
        song = example()
        with self.assertRaises(MidiError):
            edit_note_event(song, 0, 0, 120, bytes((60, 0)))

    def test_noop_preserves_dirty_flag(self):
        song = example()
        song.dirty = False
        self.assertFalse(edit_note_event(song, 0, 0, 120, bytes((60, 100))))
        self.assertFalse(song.dirty)

    def test_delete_note_on_removes_both_halves(self):
        song = example()
        self.assertEqual(delete_note_event(song, 0, 0), 2)
        self.assertEqual(len(song.tracks[0].events), 1)
        self.assertEqual(song.tracks[0].events[0].meta_type, 0x2f)

    def test_delete_note_off_removes_both_halves(self):
        song = example()
        self.assertEqual(delete_note_event(song, 0, 1), 2)
        self.assertEqual(len(song.tracks[0].events), 1)

    def test_delete_end_of_track_rejected_atomically(self):
        song = example()
        before = list(song.tracks[0].events)
        with self.assertRaises(MidiError):
            delete_note_event(song, 0, 2)
        self.assertEqual(song.tracks[0].events, before)

    def test_delete_unpaired_note_rejected(self):
        song = example()
        song.tracks[0].events.pop(1)
        with self.assertRaises(MidiError):
            delete_note_event(song, 0, 0)
        self.assertEqual(len(song.tracks[0].events), 2)

    def test_unpaired_note_rejected(self):
        song = example()
        song.tracks[0].events.pop(1)
        with self.assertRaises(MidiError):
            edit_note_event(song, 0, 0, 120, bytes((64, 100)))

if __name__ == "__main__":
    unittest.main()
