import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import unittest
from midi import Song, Track, Event, MidiError
from batch_clip_ops import edit_clips
from note_ops import paired_notes


def sample():
    return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64'), Event(240, 0x80, b'\x3c\x00'), Event(2400, 0x90, b'\x3e\x64'), Event(2640, 0x80, b'\x3e\x00'), Event(0, 0xb0, b'\x07\x64')]), Track([])])

class BatchClipTests(unittest.TestCase):
    def test_move_two_clips_uses_original_indices(self):
        s=sample(); self.assertEqual(edit_clips(s, [(0,0),(0,1)],480),2)
        self.assertEqual(sorted(s.tracks[0].events[i].tick for a,b in paired_notes(s.tracks[0]) for i in (a,b)),[480,720,2880,3120])
    def test_duplicate_two_clips(self):
        s=sample(); self.assertEqual(edit_clips(s, [(0,0),(0,1)],480,True),2)
        self.assertEqual(len(paired_notes(s.tracks[0])),4)
    def test_move_to_other_track(self):
        s=sample(); edit_clips(s,[(0,0),(0,1)],0,destination_tracks={0:1})
        self.assertEqual(len(paired_notes(s.tracks[0])),0)
        self.assertEqual(len(paired_notes(s.tracks[1])),2)
    def test_copy_to_other_track(self):
        s=sample(); edit_clips(s,[(0,0)],0,True,{0:1})
        self.assertEqual(len(paired_notes(s.tracks[0])),2)
        self.assertEqual(len(paired_notes(s.tracks[1])),1)
    def test_invalid_selection_atomic(self):
        s=sample(); before=s.to_bytes()
        with self.assertRaises(MidiError): edit_clips(s,[(0,0),(0,10)],480)
        self.assertEqual(s.to_bytes(),before); self.assertFalse(s.dirty)
    def test_negative_atomic(self):
        s=sample()
        with self.assertRaises(MidiError): edit_clips(s,[(0,0),(0,1)],-1)
        self.assertFalse(s.dirty)
    def test_duplicate_selection_rejected(self):
        s=sample()
        with self.assertRaises(MidiError): edit_clips(s,[(0,0),(0,0)],0)
        self.assertFalse(s.dirty)
    def test_empty_rejected(self):
        with self.assertRaises(MidiError): edit_clips(sample(),[],0)

if __name__ == '__main__': unittest.main()
