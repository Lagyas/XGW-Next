import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Event, Track, Song, MidiError
from velocity_ops import set_note_velocities

def example_song():
    return Song(0, 480, [Track([
        Event(0, 0x90, bytes((60, 100)), order=0),
        Event(120, 0x80, bytes((60, 0)), order=1),
        Event(240, 0x91, bytes((65, 80)), order=2),
        Event(360, 0x81, bytes((65, 0)), order=3),
        Event(360, 0xff, b"", 0x2f, 4),
    ])])

class VelocityOpsTests(unittest.TestCase):
    def test_multiple_velocity_edits_roundtrip(self):
        song = example_song()
        self.assertEqual(set_note_velocities(song, 0, {0: 42, 2: 127}), 2)
        parsed = Song.from_bytes(song.to_bytes())
        self.assertEqual(parsed.tracks[0].events[0].data, bytes((60, 42)))
        self.assertEqual(parsed.tracks[0].events[2].data, bytes((65, 127)))
        self.assertEqual(parsed.tracks[0].events[1].data, bytes((60, 0)))

    def test_reject_out_of_range_atomically(self):
        song = example_song()
        previous = [event.data for event in song.tracks[0].events]
        with self.assertRaises(MidiError):
            set_note_velocities(song, 0, {0: 50, 2: 0})
        self.assertEqual([event.data for event in song.tracks[0].events], previous)

    def test_reject_note_off_and_unmatched_note(self):
        song = example_song()
        with self.assertRaises(MidiError):
            set_note_velocities(song, 0, {1: 90})
        with self.assertRaises(MidiError):
            set_note_velocities(song, 0, {4: 90})

    def test_unchanged_note_timing(self):
        song = example_song()
        before = [(event.tick, event.status) for event in song.tracks[0].events]
        set_note_velocities(song, 0, {0: 20})
        self.assertEqual([(event.tick, event.status) for event in song.tracks[0].events], before)

if __name__ == "__main__":
    unittest.main()
