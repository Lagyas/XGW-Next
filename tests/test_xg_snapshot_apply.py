import unittest
from midi import Song, Track, Event, MidiError
from xg_effects import effect_parameters_at_tick
from xg_snapshot_apply import apply_snapshot_parameter

class SnapshotApplyTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(0, 480, [Track([Event(960, 0xff, b'', 0x2f)])])

    def test_insert_selected_value(self):
        apply_snapshot_parameter(self.song, {('reverb', 3): b'\x20'}, 'reverb', 3, 120)
        self.assertEqual(effect_parameters_at_tick(self.song, 120)[('reverb', 3)], b'\x20')

    def test_missing_parameter_does_not_mutate(self):
        before = list(self.song.tracks[0].events)
        with self.assertRaises(MidiError):
            apply_snapshot_parameter(self.song, {}, 'reverb', 3, 120)
        self.assertEqual(self.song.tracks[0].events, before)

    def test_invalid_destination_does_not_mutate(self):
        before = list(self.song.tracks[0].events)
        with self.assertRaises(MidiError):
            apply_snapshot_parameter(self.song, {('chorus', 2): b'\x10'}, 'chorus', 2, 120, track_index=9)
        self.assertEqual(self.song.tracks[0].events, before)

    def test_invalid_snapshot_byte_does_not_mutate(self):
        before = list(self.song.tracks[0].events)
        with self.assertRaises(MidiError):
            apply_snapshot_parameter(self.song, {('variation', 3): [255]}, 'variation', 3, 120)
        self.assertEqual(self.song.tracks[0].events, before)
