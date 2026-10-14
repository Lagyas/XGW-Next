import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import unittest
from midi import Song, Track, Event, MidiError
from batch_clip_ops import edit_clips


def song():
    return Song(1,480,[Track([Event(0,0x90,b'\x3c\x64'),Event(240,0x80,b'\x3c\x00'),Event(10,0xb0,b'\x07\x60'),Event(20,0xc0,b'\x05'),Event(30,0xe0,b'\x00\x40'),Event(40,0xf0,b'\x43\x10'),Event(15,0xff,b'\x07',0x51),Event(400,0xb0,b'\x07\x40')]),Track([])])

class ClipControllers(unittest.TestCase):
    def test_default_leaves_controllers(self):
        s=song(); edit_clips(s,[(0,0)],480)
        self.assertEqual(next(e.tick for e in s.tracks[0].events if e.status==0xb0 and e.data[1]==0x60),10)
    def test_move_controllers(self):
        s=song(); edit_clips(s,[(0,0)],480,include_events=True)
        self.assertEqual(sorted(e.tick for e in s.tracks[0].events if e.status in (0xb0,0xc0,0xe0,0xf0)),[400,490,500,510,520])
    def test_meta_preserved(self):
        s=song(); edit_clips(s,[(0,0)],480,include_events=True)
        self.assertEqual(next(e.tick for e in s.tracks[0].events if e.status==0xff),15)
    def test_copy_to_other_track(self):
        s=song(); edit_clips(s,[(0,0)],480,True,{0:1},include_events=True)
        self.assertEqual(sum(e.status==0xf0 for e in s.tracks[0].events),1)
        self.assertEqual(sum(e.status==0xf0 for e in s.tracks[1].events),1)
    def test_move_to_other_track(self):
        s=song(); edit_clips(s,[(0,0)],0,False,{0:1},include_events=True)
        self.assertEqual(sum(e.status==0xc0 for e in s.tracks[0].events),0)
        self.assertEqual(sum(e.status==0xc0 for e in s.tracks[1].events),1)
    def test_invalid_offset_atomic(self):
        s=song(); before=s.to_bytes()
        with self.assertRaises(MidiError): edit_clips(s,[(0,0)],-1,include_events=True)
        self.assertEqual(s.to_bytes(),before)
    def test_invalid_flag_atomic(self):
        s=song(); before=s.to_bytes()
        with self.assertRaises(MidiError): edit_clips(s,[(0,0)],0,include_events=1)
        self.assertEqual(s.to_bytes(),before)

if __name__=='__main__': unittest.main()
