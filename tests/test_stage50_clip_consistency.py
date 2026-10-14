import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import unittest
from midi import Song, Track, Event, MidiError
from batch_clip_ops import edit_clips


def song():
    return Song(1, 480, [Track([
        Event(0, 0x90, b'\x3c\x60'), Event(240, 0x80, b'\x3c\x00'),
        Event(60, 0xb0, b'\x07\x40'), Event(120, 0xc0, b'\x05'),
        Event(180, 0xf0, b'\x7e\x7f'),
    ]), Track([])])

class ClipConsistencyTests(unittest.TestCase):
    def test_single_clip_move_carries_events(self):
        s = song()
        edit_clips(s, [(0, 0)], 480, include_events=True)
        self.assertEqual(sorted((e.status, e.tick) for e in s.tracks[0].events),
                         sorted([(0x90,480),(0x80,720),(0xb0,540),(0xc0,600),(0xf0,660)]))

    def test_single_clip_copy_carries_events(self):
        s = song()
        edit_clips(s, [(0, 0)], 480, duplicate=True, include_events=True)
        self.assertEqual(len(s.tracks[0].events), 10)

    def test_single_clip_cross_track_moves_events(self):
        s = song()
        edit_clips(s, [(0, 0)], 0, destination_tracks={0:1}, include_events=True)
        self.assertEqual(len(s.tracks[0].events), 0)
        self.assertEqual(len(s.tracks[1].events), 5)

    def test_single_clip_invalid_target_is_atomic(self):
        s = song()
        original = s.to_bytes()
        with self.assertRaises(MidiError):
            edit_clips(s, [(0,0)], 0, destination_tracks={0:4}, include_events=True)
        self.assertEqual(s.to_bytes(), original)
        self.assertFalse(s.dirty)
