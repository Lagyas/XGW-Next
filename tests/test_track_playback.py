import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, Track, Event
from midi_output import timed_messages

class PlaybackFilterTests(unittest.TestCase):
    def test_muted_track_keeps_tempo(self):
        song = Song(1, 480, [
            Track([Event(0, 0xff, bytes((0x03, 0xd0, 0x90)), 0x51)]),
            Track([Event(0, 0x90, bytes((60, 100))),
                   Event(480, 0x80, bytes((60, 0)))]),
            Track([Event(0, 0x91, bytes((62, 100))),
                   Event(480, 0x81, bytes((62, 0)))])
        ])
        messages = list(timed_messages(song, enabled_tracks={1}))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0][1][0], 0x90)
        self.assertAlmostEqual(messages[1][0], 0.25)
        self.assertEqual(len(list(timed_messages(song, enabled_tracks=set()))), 0)

if __name__ == "__main__":
    unittest.main()
