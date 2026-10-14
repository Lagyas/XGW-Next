import unittest
from midi import Song, Track, Event, MidiError
from note_ops import insert_note, paired_notes, transform_notes
from xg_drums import GM_DRUM_NOTES


class DrumTransformTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [Track([])])
        insert_note(self.song, 0, 240, 120, 36, channel=10, velocity=90)
        insert_note(self.song, 0, 480, 120, 38, channel=10, velocity=100)

    def test_move_two_hits_preserves_duration_and_velocity(self):
        pairs = paired_notes(self.song.tracks[0])
        self.assertEqual(transform_notes(self.song, 0, pairs, 120, 0), 2)
        notes = [(self.song.tracks[0].events[a], self.song.tracks[0].events[b])
                 for a, b in paired_notes(self.song.tracks[0])]
        self.assertEqual(sorted((a.tick, b.tick, a.data[1]) for a, b in notes),
                         [(360, 480, 90), (600, 720, 100)])

    def test_copy_does_not_remove_originals(self):
        pairs = paired_notes(self.song.tracks[0])
        self.assertEqual(transform_notes(self.song, 0, pairs, 960, 0, duplicate=True), 2)
        self.assertEqual(len(paired_notes(self.song.tracks[0])), 4)

    def test_invalid_transform_is_atomic(self):
        pairs = paired_notes(self.song.tracks[0])
        before = [(e.tick, e.data) for e in self.song.tracks[0].events]
        with self.assertRaises(MidiError):
            transform_notes(self.song, 0, pairs, -500, 0)
        self.assertEqual([(e.tick, e.data) for e in self.song.tracks[0].events], before)

    def test_drum_map_restricts_targets(self):
        self.assertIn(36, GM_DRUM_NOTES)
        self.assertNotIn(127, GM_DRUM_NOTES)
