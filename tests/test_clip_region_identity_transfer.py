import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from batch_clip_ops import edit_clips
from test_clip_region_transfer import fixture


class RegionIdentityTransferTests(unittest.TestCase):
    def test_move_keeps_uuid(self):
        song = fixture()
        song.tracks[0].clip_region_ids = ['a' * 32, 'b' * 32]
        edit_clips(song, [(0, 1)], -1920, destination_tracks={0: 1})
        self.assertEqual(song.tracks[0].clip_region_ids, ['a' * 32])
        self.assertEqual(song.tracks[1].clip_region_ids[0], 'b' * 32)

    def test_copy_creates_new_uuid(self):
        song = fixture()
        song.tracks[0].clip_region_ids = ['a' * 32, 'b' * 32]
        edit_clips(song, [(0, 1)], -1920, duplicate=True, destination_tracks={0: 1})
        self.assertEqual(song.tracks[0].clip_region_ids, ['a' * 32, 'b' * 32])
        self.assertNotIn('b' * 32, song.tracks[1].clip_region_ids)

    def test_collision_clears_region_ids(self):
        song = fixture()
        song.tracks[1].clip_regions = [(960, 1080)]
        song.tracks[1].clip_region_ids = ['c' * 32]
        edit_clips(song, [(0, 1)], -1440, destination_tracks={0: 1})
        self.assertFalse(hasattr(song.tracks[1], 'clip_region_ids'))

    def test_batch_move_retains_ids_in_sorted_order(self):
        song = fixture()
        song.tracks[0].clip_region_ids = ['a' * 32, 'b' * 32]
        edit_clips(song, [(0, 0), (0, 1)], 3000, destination_tracks={0: 1})
        self.assertEqual(song.tracks[1].clip_region_ids[1:], ['a' * 32, 'b' * 32])

if __name__ == '__main__':
    unittest.main()
