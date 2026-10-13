import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Event, Track, Song, MidiError
from mixer_ops import channel_values, set_channel_values

class MixerOpsTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [Track([Event(0, 0xff, b"", 0x2f, 0)])])

    def test_defaults(self):
        self.assertEqual(channel_values(self.song, 1)["Pan"], 64)
        self.assertEqual(channel_values(self.song, 1)["Volume"], 100)

    def test_roundtrip(self):
        set_channel_values(self.song, 0, 2, {"Volume": 75, "Pan": 32}, 240)
        parsed = Song.from_bytes(self.song.to_bytes())
        self.assertEqual(channel_values(parsed, 2, 239)["Volume"], 100)
        self.assertEqual(channel_values(parsed, 2, 240)["Volume"], 75)
        self.assertEqual(channel_values(parsed, 2, 240)["Pan"], 32)

    def test_replace_same_tick(self):
        set_channel_values(self.song, 0, 1, {"Volume": 40})
        set_channel_values(self.song, 0, 1, {"Volume": 90})
        events = [e for e in self.song.tracks[0].events
                  if e.status == 0xb0 and e.data[0] == 7]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].data[1], 90)

    def test_reject_invalid_without_changes(self):
        before = len(self.song.tracks[0].events)
        with self.assertRaises(MidiError):
            set_channel_values(self.song, 0, 1, {"Volume": 150})
        with self.assertRaises(MidiError):
            set_channel_values(self.song, 0, 17, {"Volume": 80})
        self.assertEqual(len(self.song.tracks[0].events), before)

if __name__ == "__main__":
    unittest.main()
