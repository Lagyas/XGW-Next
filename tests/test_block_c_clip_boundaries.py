import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'editor'))
import unittest
from midi import Song,Track,Event,MidiError
from clip_boundaries import split_sustained_notes,trim_clip_notes
from velocity_ops import scale_note_velocities
from note_ops import paired_notes

def sample():
    return Song(1,480,[Track([Event(0,0x90,b'\x3c\x64'),Event(480,0x80,b'\x3c\x00'),
        Event(50,0xb0,b'\x07\x40'),Event(200,0x90,b'\x3e\x50'),Event(400,0x80,b'\x3e\x00'),
        Event(480,0xff,b'',0x2f)])])
class BlockC(unittest.TestCase):
    def test_split_crossing_notes(self):
        s=sample(); self.assertEqual(split_sustained_notes(s,0,0,240),2)
        self.assertEqual(len(paired_notes(s.tracks[0])),4)
        self.assertEqual(sorted((s.tracks[0].events[a].tick,s.tracks[0].events[b].tick) for a,b in paired_notes(s.tracks[0])),[(0,240),(200,240),(240,400),(240,480)])
    def test_split_no_crossing_is_noop(self):
        s=sample(); self.assertEqual(split_sustained_notes(s,0,0,400),1)
    def test_split_invalid_atomic(self):
        s=sample(); before=s.to_bytes()
        with self.assertRaises(MidiError): split_sustained_notes(s,0,0,0)
        self.assertEqual(s.to_bytes(),before)
    def test_trim_clips_notes_and_preserves_cc(self):
        s=sample(); self.assertEqual(trim_clip_notes(s,0,0,100,300),2)
        self.assertEqual(sorted((s.tracks[0].events[a].tick,s.tracks[0].events[b].tick) for a,b in paired_notes(s.tracks[0])),[(100,300),(200,300)])
        self.assertEqual(next(e.tick for e in s.tracks[0].events if e.status==0xb0),50)
    def test_trim_invalid_atomic(self):
        s=sample(); before=s.to_bytes()
        with self.assertRaises(MidiError): trim_clip_notes(s,0,0,200,600)
        self.assertEqual(s.to_bytes(),before)
    def test_velocity_scale(self):
        s=sample(); self.assertEqual(scale_note_velocities(s,0,[0,3],200),2)
        self.assertEqual(s.tracks[0].events[0].data[1],127)
        self.assertEqual(s.tracks[0].events[3].data[1],127)
    def test_velocity_invalid_atomic(self):
        s=sample(); before=s.to_bytes()
        with self.assertRaises(MidiError): scale_note_velocities(s,0,[0,100],200)
        self.assertEqual(s.to_bytes(),before)
    def test_roundtrip_split_trim(self):
        s=sample(); split_sustained_notes(s,0,0,240)
        self.assertEqual(len(Song.from_bytes(s.to_bytes()).tracks[0].events),len(s.tracks[0].events))
if __name__=='__main__':unittest.main()
