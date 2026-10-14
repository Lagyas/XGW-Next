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

    def test_read_rejects_boolean_channel(self):
        with self.assertRaises(MidiError):
            channel_values(self.song, True)

    def test_read_rejects_boolean_tick(self):
        with self.assertRaises(MidiError):
            channel_values(self.song, 1, False)

    def test_read_rejects_out_of_range_tick(self):
        with self.assertRaises(MidiError):
            channel_values(self.song, 1, 0x10000000)

    def test_write_rejects_boolean_track_without_mutation(self):
        before = self.song.to_bytes()
        with self.assertRaises(MidiError):
            set_channel_values(self.song, False, 1, {"Volume": 50})
        self.assertEqual(self.song.to_bytes(), before)

    def test_write_rejects_boolean_tick_without_mutation(self):
        before = self.song.to_bytes()
        with self.assertRaises(MidiError):
            set_channel_values(self.song, 0, 1, {"Pan": 20}, True)
        self.assertEqual(self.song.to_bytes(), before)

    def test_roundtrip(self):
        set_channel_values(self.song, 0, 2, {"Volume": 75, "Pan": 32}, 240)
        parsed = Song.from_bytes(self.song.to_bytes())
        self.assertEqual(channel_values(parsed, 2, 239)["Volume"], 100)
        self.assertEqual(channel_values(parsed, 2, 240)["Volume"], 75)
        self.assertEqual(channel_values(parsed, 2, 240)["Pan"], 32)

    def test_variation_send_cc94_roundtrip(self):
        self.assertEqual(channel_values(self.song, 3)["Variation"], 0)
        set_channel_values(self.song, 0, 3, {"Variation": 78}, 120)
        events = [e for e in self.song.tracks[0].events if e.status == 0xb2 and e.data == bytes((94, 78))]
        self.assertEqual(len(events), 1)
        parsed = Song.from_bytes(self.song.to_bytes())
        self.assertEqual(channel_values(parsed, 3, 119)["Variation"], 0)
        self.assertEqual(channel_values(parsed, 3, 120)["Variation"], 78)

    def test_variation_does_not_change_other_sends(self):
        set_channel_values(self.song, 0, 1, {"Reverb": 50, "Chorus": 35}, 0)
        set_channel_values(self.song, 0, 1, {"Variation": 100}, 0)
        values = channel_values(self.song, 1)
        self.assertEqual((values["Reverb"], values["Chorus"], values["Variation"]), (50, 35, 100))

    def test_replace_same_tick(self):
        set_channel_values(self.song, 0, 1, {"Volume": 40})
        set_channel_values(self.song, 0, 1, {"Volume": 90})
        events = [e for e in self.song.tracks[0].events
                  if e.status == 0xb0 and e.data[0] == 7]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].data[1], 90)

    def test_changed_channel_does_not_touch_other_channels(self):
        set_channel_values(self.song, 0, 1, {"Volume": 66}, 0)
        before = len(self.song.tracks[0].events)
        set_channel_values(self.song, 0, 1, {"Pan": 20}, 0)
        self.assertEqual(len(self.song.tracks[0].events), before + 1)
        self.assertEqual(channel_values(self.song, 1)["Volume"], 66)
        self.assertEqual(channel_values(self.song, 1)["Pan"], 20)
        self.assertEqual(channel_values(self.song, 2)["Volume"], 100)
        self.assertFalse(any(e.status == 0xb1 for e in self.song.tracks[0].events))

    def test_edit_does_not_change_unrelated_tracks(self):
        self.song.tracks.append(Track([Event(0, 0xb1, bytes((7, 45)), order=0)]))
        other_before = [(e.tick, e.status, e.data) for e in self.song.tracks[1].events]
        set_channel_values(self.song, 0, 1, {"Chorus": 33}, 120)
        self.assertEqual(
            [(e.tick, e.status, e.data) for e in self.song.tracks[1].events],
            other_before)

    def test_reject_invalid_without_changes(self):
        before = len(self.song.tracks[0].events)
        with self.assertRaises(MidiError):
            set_channel_values(self.song, 0, 1, {"Volume": 150})
        with self.assertRaises(MidiError):
            set_channel_values(self.song, 0, 17, {"Volume": 80})
        self.assertEqual(len(self.song.tracks[0].events), before)

if __name__ == "__main__":
    unittest.main()
