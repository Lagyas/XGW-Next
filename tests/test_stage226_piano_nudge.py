"""Headless regression coverage for note nudging used by Piano Roll shortcuts."""
import unittest
from midi import Song, Track, Event, MidiError
from note_ops import transform_notes

class PianoNudgeTests(unittest.TestCase):
    def song(self, pitch=60, tick=120):
        return Song(1, 480, [Track([Event(tick, 0x90, bytes([pitch, 90]), order=0),
                                    Event(tick + 240, 0x80, bytes([pitch, 0]), order=1)])])

    def test_pitch_and_time_move_both_note_ends(self):
        song = self.song()
        self.assertEqual(transform_notes(song, 0, [(0, 1)], delta_ticks=120, delta_pitch=1), 1)
        self.assertEqual([(e.tick, e.data[0]) for e in song.tracks[0].events], [(240, 61), (480, 61)])

    def test_invalid_negative_tick_does_not_mutate(self):
        song = self.song(tick=0)
        before = [(e.tick, e.data) for e in song.tracks[0].events]
        with self.assertRaises(MidiError):
            transform_notes(song, 0, [(0, 1)], delta_ticks=-120)
        self.assertEqual([(e.tick, e.data) for e in song.tracks[0].events], before)
        self.assertFalse(song.dirty)

    def test_pitch_overflow_does_not_mutate(self):
        song = self.song(pitch=127)
        before = [(e.tick, e.data) for e in song.tracks[0].events]
        with self.assertRaises(MidiError):
            transform_notes(song, 0, [(0, 1)], delta_pitch=1)
        self.assertEqual([(e.tick, e.data) for e in song.tracks[0].events], before)
        self.assertFalse(song.dirty)

if __name__ == '__main__':
    unittest.main()
