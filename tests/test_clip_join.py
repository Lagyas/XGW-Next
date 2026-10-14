import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import unittest
from midi import Song, Track, Event, MidiError
from arrangement import track_clips
from clip_join import close_clip_gap


def make_song():
    return Song(1, 480, [Track([
        Event(0, 0x90, b'\x3c\x64'), Event(240, 0x80, b'\x3c\x00'),
        Event(2400, 0x90, b'\x3e\x64'), Event(2640, 0x80, b'\x3e\x00'),
        Event(2410, 0xb0, b'\x07\x60'), Event(2450, 0xff, b'\x00', 0x51),
    ])])


class ClipJoinTests(unittest.TestCase):
    def test_close_gap_merges_inferred_clips(self):
        s = make_song()
        self.assertEqual(len(track_clips(s.tracks[0], s.division)), 2)
        self.assertEqual(close_clip_gap(s, 0, 0), 1)
        self.assertEqual(len(track_clips(s.tracks[0], s.division)), 1)
        self.assertEqual(next(e.tick for e in s.tracks[0].events if e.status == 0x90 and e.data[0] == 62), 240)
        self.assertEqual(next(e.tick for e in s.tracks[0].events if e.status == 0xb0), 250)
        self.assertEqual(next(e.tick for e in s.tracks[0].events if e.status == 0xff), 2450)

    def test_leave_controllers(self):
        s = make_song()
        close_clip_gap(s, 0, 0, include_events=False)
        self.assertEqual(next(e.tick for e in s.tracks[0].events if e.status == 0xb0), 2410)

    def test_gap_allowed_below_one_bar(self):
        s = make_song()
        close_clip_gap(s, 0, 0, gap=100)
        self.assertEqual(next(e.tick for e in s.tracks[0].events if e.status == 0x90 and e.data[0] == 62), 340)
        self.assertEqual(len(track_clips(s.tracks[0], s.division)), 1)

    def test_invalid_gap_atomic(self):
        s = make_song(); original = s.to_bytes()
        with self.assertRaises(MidiError):
            close_clip_gap(s, 0, 0, gap=1920)
        self.assertEqual(s.to_bytes(), original)

    def test_no_next_clip_atomic(self):
        s = make_song(); original = s.to_bytes()
        with self.assertRaises(MidiError):
            close_clip_gap(s, 0, 1)
        self.assertEqual(s.to_bytes(), original)

    def test_reject_bool_index(self):
        s = make_song()
        with self.assertRaises(MidiError):
            close_clip_gap(s, True, 0)

if __name__ == '__main__': unittest.main()
