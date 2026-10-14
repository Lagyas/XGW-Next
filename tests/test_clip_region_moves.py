import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event
from arrangement import track_clips
from batch_clip_ops import edit_clips


def fixture():
    track = Track([Event(0, 0x90, b'\x3c\x64'), Event(240, 0x80, b'\x3c\x00'),
                   Event(2400, 0x90, b'\x3e\x64'), Event(2640, 0x80, b'\x3e\x00')])
    track.clip_regions = [(0, 120), (120, 240), (2400, 2640)]
    return Song(1, 480, [track, Track([])])


class ClipRegionMoveTests(unittest.TestCase):
    def test_preserve_split_boundaries_when_moving_unrelated_clip(self):
        song = fixture()
        edit_clips(song, [(0, 2)], 480)
        self.assertEqual(track_clips(song.tracks[0], 480), [(0, 120), (120, 240), (2880, 3120)])

    def test_preserve_selected_split_region_when_moved_into_gap(self):
        song = fixture()
        edit_clips(song, [(0, 0)], 480)
        self.assertEqual(track_clips(song.tracks[0], 480), [(120, 240), (480, 600), (2400, 2640)])

    def test_overlapping_new_regions_fall_back_safely(self):
        song = fixture()
        edit_clips(song, [(0, 2)], -2300)
        self.assertFalse(hasattr(song.tracks[0], 'clip_regions'))

    def test_cross_track_move_preserves_remaining_regions(self):
        song = fixture()
        edit_clips(song, [(0, 2)], 0, destination_tracks={0: 1})
        self.assertEqual(track_clips(song.tracks[0], 480), [(0, 120), (120, 240)])
        self.assertEqual(track_clips(song.tracks[1], 480), [(2400, 2640)])

    def test_duplicate_preserves_regions(self):
        song = fixture()
        edit_clips(song, [(0, 2)], 480, duplicate=True)
        self.assertEqual(track_clips(song.tracks[0], 480), [(0, 120), (120, 240), (2400, 2640), (2880, 3120)])

    def test_zero_delta_preserves_regions(self):
        song = fixture()
        edit_clips(song, [(0, 2)], 0)
        self.assertEqual(track_clips(song.tracks[0], 480), [(0, 120), (120, 240), (2400, 2640)])
