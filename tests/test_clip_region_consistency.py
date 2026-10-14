import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from clip_regions import split_region
from batch_clip_ops import edit_clips
from arrangement import track_clips


def make_song():
    return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64'),
                                Event(480, 0x80, b'\x3c\x00')]), Track([])])


class ClipRegionConsistencyTests(unittest.TestCase):
    def test_move_preserves_disjoint_explicit_regions(self):
        s = make_song(); split_region(s, 0, 0, 240)
        edit_clips(s, [(0, 0)], 960)
        self.assertEqual(track_clips(s.tracks[0], 480), [(240, 480), (960, 1200)])

    def test_copy_preserves_regions(self):
        s = make_song(); split_region(s, 0, 0, 240)
        edit_clips(s, [(0, 0)], 960, duplicate=True)
        self.assertEqual(track_clips(s.tracks[0], 480), [(0, 240), (240, 480), (960, 1200)])

    def test_cross_track_transfers_region(self):
        s = make_song(); split_region(s, 0, 0, 240)
        s.tracks[1].clip_regions = [(0, 100)]
        edit_clips(s, [(0, 0)], 960, destination_tracks={0: 1})
        self.assertEqual(track_clips(s.tracks[0], 480), [(240, 480)])
        self.assertEqual(track_clips(s.tracks[1], 480), [(0, 100), (960, 1200)])

    def test_zero_delta_keeps_regions(self):
        s = make_song(); split_region(s, 0, 0, 240)
        edit_clips(s, [(0, 0)], 0)
        self.assertEqual(track_clips(s.tracks[0], 480), [(0, 240), (240, 480)])

    def test_overlapping_note_tails_rejected_atomically(self):
        s = make_song(); s.tracks[0].clip_regions = [(0, 240), (240, 480)]
        # A note beginning in the first region is not selected by the second.
        # Independent events must still remain untouched.
        before = s.to_bytes()
        with self.assertRaises(MidiError):
            edit_clips(s, [(0, 0), (0, 1)], 960)
        self.assertEqual(s.to_bytes(), before)
