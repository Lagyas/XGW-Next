import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event
from arrangement import track_clips
from batch_clip_ops import edit_clips


def fixture():
    a = Track([Event(0, 0x90, b'\x3c\x64'), Event(120, 0x80, b'\x3c\x00'),
               Event(2400, 0x90, b'\x3e\x64'), Event(2520, 0x80, b'\x3e\x00')])
    a.clip_regions = [(0, 120), (2400, 2520)]
    b = Track([Event(960, 0x90, b'\x40\x64'), Event(1080, 0x80, b'\x40\x00')])
    return Song(1, 480, [a, b])


class ClipRegionTransferTests(unittest.TestCase):
    def test_cross_track_move_retains_unselected_and_adds_target(self):
        s = fixture()
        edit_clips(s, [(0, 1)], -1920, destination_tracks={0: 1})
        self.assertEqual(track_clips(s.tracks[0], 480), [(0, 120)])
        self.assertEqual(track_clips(s.tracks[1], 480), [(480, 600), (960, 1080)])

    def test_cross_track_duplicate_preserves_original_and_target(self):
        s = fixture()
        edit_clips(s, [(0, 1)], -1920, duplicate=True, destination_tracks={0: 1})
        self.assertEqual(track_clips(s.tracks[0], 480), [(0, 120), (2400, 2520)])
        self.assertEqual(track_clips(s.tracks[1], 480), [(480, 600), (960, 1080)])

    def test_destination_overlap_falls_back_only_on_destination(self):
        s = fixture()
        edit_clips(s, [(0, 1)], -1440, destination_tracks={0: 1})
        self.assertEqual(track_clips(s.tracks[0], 480), [(0, 120)])
        self.assertFalse(hasattr(s.tracks[1], 'clip_regions'))

    def test_multiple_clip_transfer_preserves_all_boundaries(self):
        s = fixture()
        edit_clips(s, [(0, 0), (0, 1)], 3000, destination_tracks={0: 1})
        self.assertEqual(track_clips(s.tracks[0], 480), [])
        self.assertEqual(track_clips(s.tracks[1], 480), [(960, 1080), (3000, 3120), (5400, 5520)])


if __name__ == '__main__':
    unittest.main()
