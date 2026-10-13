import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, Track, Event, MidiError
from clip_ops import edit_clip
from note_ops import paired_notes

def song():
    return Song(0, 480, [Track([
        Event(0, 0x90, bytes((60, 100)), order=0),
        Event(240, 0x80, bytes((60, 0)), order=1),
        Event(0, 0xb0, bytes((7, 100)), order=2),
        Event(2400, 0x90, bytes((62, 100)), order=3),
        Event(2640, 0x80, bytes((62, 0)), order=4),
    ])])

class ClipOpsTests(unittest.TestCase):
    def test_move_only_selected_notes(self):
        s = song()
        self.assertEqual(edit_clip(s, 0, 0, 480), 1)
        self.assertEqual(sorted(s.tracks[0].events[i].tick for pair in paired_notes(s.tracks[0]) for i in pair),
                         [480, 720, 2400, 2640])
        self.assertEqual(s.tracks[0].events[2].tick, 0)
        self.assertTrue(s.dirty)

    def test_duplicate_preserves_original(self):
        s = song()
        self.assertEqual(edit_clip(s, 0, 0, 480, True), 1)
        self.assertEqual(len(paired_notes(s.tracks[0])), 3)

    def test_copy_to_another_track(self):
        s = song()
        s.tracks.append(Track([]))
        count = edit_clip(s, 0, 0, 480, duplicate=True, destination_track=1)
        self.assertEqual(count, 1)
        self.assertEqual(len(paired_notes(s.tracks[0])), 2)
        self.assertEqual(len(paired_notes(s.tracks[1])), 1)
        self.assertEqual([e.tick for e in s.tracks[1].events], [480, 720])

    def test_move_to_another_track(self):
        s = song()
        s.tracks.append(Track([]))
        count = edit_clip(s, 0, 0, 0, destination_track=1)
        self.assertEqual(count, 1)
        self.assertEqual(len(paired_notes(s.tracks[0])), 1)
        self.assertEqual(len(paired_notes(s.tracks[1])), 1)
        self.assertEqual([e.tick for e in s.tracks[1].events], [0, 240])

    def test_invalid_destination_does_not_mutate(self):
        s = song()
        with self.assertRaises(MidiError):
            edit_clip(s, 0, 0, 480, destination_track=5)
        self.assertFalse(s.dirty)

    def test_end_of_track_after_move(self):
        s = song()
        s.tracks[0].events.append(Event(2640, 0xff, b"", 0x2f, 5))
        edit_clip(s, 0, 1, 960)
        restored = Song.from_bytes(s.to_bytes())
        self.assertEqual(restored.tracks[0].events[-1].meta_type, 0x2f)
        self.assertEqual(restored.tracks[0].events[-1].tick, 3600)

    def test_negative_offset_rejected_without_changes(self):
        s = song()
        with self.assertRaises(MidiError):
            edit_clip(s, 0, 0, -480)
        self.assertFalse(s.dirty)

if __name__ == "__main__":
    unittest.main()
