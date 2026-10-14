import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from arrangement import track_clips
from clip_regions import split_region, merge_regions, reset_regions


def song():
    return Song(1, 480, [Track([
        Event(0, 0x90, b'\x3c\x64'), Event(480, 0x80, b'\x3c\x00'),
        Event(2400, 0x90, b'\x3e\x64'), Event(2880, 0x80, b'\x3e\x00'),
        Event(100, 0xb0, b'\x07\x50')])])

class ClipRegionTests(unittest.TestCase):
    def test_split_keeps_all_events(self):
        s = song(); before = [(e.tick,e.status,e.data) for e in s.tracks[0].events]
        self.assertEqual(split_region(s,0,0,240),3)
        self.assertEqual(track_clips(s.tracks[0],480),[(0,240),(240,480),(2400,2880)])
        self.assertEqual(before,[(e.tick,e.status,e.data) for e in s.tracks[0].events])
    def test_merge_across_silence(self):
        s = song(); merge_regions(s,0,0)
        self.assertEqual(track_clips(s.tracks[0],480),[(0,2880)])
    def test_split_then_merge(self):
        s = song(); split_region(s,0,0,240); merge_regions(s,0,0)
        self.assertEqual(track_clips(s.tracks[0],480)[0],(0,480))
    def test_reset(self):
        s = song(); split_region(s,0,0,240); reset_regions(s,0)
        self.assertEqual(len(track_clips(s.tracks[0],480)),2)
    def test_invalid_is_atomic(self):
        s = song()
        with self.assertRaises(MidiError): split_region(s,0,0,480)
        self.assertFalse(hasattr(s.tracks[0],'clip_regions'))
    def test_no_merge_after_last(self):
        s = song()
        with self.assertRaises(MidiError): merge_regions(s,0,1)
    def test_reject_bool(self):
        s = song()
        with self.assertRaises(MidiError): split_region(s,0,0,True)
    def test_midi_roundtrip_loses_regions_but_preserves_notes(self):
        s = song(); split_region(s,0,0,240)
        s.dirty=True
        loaded=Song.from_bytes(s.to_bytes())
        self.assertEqual(len(track_clips(loaded.tracks[0],480)),2)
        self.assertEqual(len(loaded.tracks[0].events),len(s.tracks[0].events))
