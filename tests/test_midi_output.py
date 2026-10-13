import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, Track, Event, MidiError
from midi_output import timed_messages

class MidiOutputTests(unittest.TestCase):
    def test_default_tempo(self):
        song = Song(0, 480, [Track([
            Event(0, 0x90, bytes((60, 100)), order=0),
            Event(480, 0x80, bytes((60, 0)), order=1)
        ])])
        self.assertEqual(list(timed_messages(song)),
                         [(0.0, bytes((0x90, 60, 100))), (0.5, bytes((0x80, 60, 0)))])

    def test_tempo_change(self):
        song = Song(1, 480, [
            Track([Event(480, 0xff, (1000000).to_bytes(3, "big"), 0x51, 0)]),
            Track([
                Event(0, 0x90, bytes((60, 100)), order=0),
                Event(960, 0x80, bytes((60, 0)), order=1),
            ])
        ])
        events = list(timed_messages(song))
        self.assertEqual(events[0][0], 0)
        self.assertAlmostEqual(events[1][0], 1.5)

    def test_sysex_not_sent(self):
        song = Song(0, 480, [Track([
            Event(0, 0xf0, b"\x43\x10\x4c", order=0),
            Event(0, 0x90, bytes((64, 90)), order=1)
        ])])
        self.assertEqual(len(list(timed_messages(song))), 1)

    def test_smpte_rejected(self):
        song = Song(0, 0xe728, [Track([])])
        with self.assertRaises(MidiError):
            list(timed_messages(song))

if __name__ == "__main__":
    unittest.main()
