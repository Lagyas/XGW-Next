import unittest
from midi import Song, Track, Event, MidiError
from xg_effects import effect_parameters_at_tick
from xg_snapshot_apply import apply_snapshot_batch

class XGSnapshotBatchTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(0, 480, [Track([])])
        self.values = {('reverb', 3): b'\x10', ('chorus', 2): b'\x20'}

    def test_two_parameters(self):
        self.assertEqual(apply_snapshot_batch(self.song, self.values, list(self.values), 100), 2)
        self.assertEqual(effect_parameters_at_tick(self.song, 100), self.values)

    def test_replace_is_idempotent(self):
        apply_snapshot_batch(self.song, self.values, list(self.values), 100)
        apply_snapshot_batch(self.song, self.values, list(self.values), 100, replace=True)
        self.assertEqual(len(self.song.tracks[0].events), 2)

    def test_invalid_batch_is_atomic(self):
        before = list(self.song.tracks[0].events)
        with self.assertRaises(MidiError):
            apply_snapshot_batch(self.song, self.values, [('reverb', 3), ('chorus', 7)], 100)
        self.assertEqual(self.song.tracks[0].events, before)
        self.assertFalse(self.song.dirty)

    def test_duplicate_rejected(self):
        with self.assertRaises(MidiError):
            apply_snapshot_batch(self.song, self.values, [('reverb', 3)] * 2, 100)

    def test_preserves_other_device(self):
        apply_snapshot_batch(self.song, self.values, [('reverb', 3)], 100, device=1)
        apply_snapshot_batch(self.song, self.values, [('reverb', 3)], 100, device=0, replace=True)
        self.assertEqual(len(self.song.tracks[0].events), 2)

if __name__ == '__main__':
    unittest.main()
