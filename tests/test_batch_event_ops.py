import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import unittest
from midi import Song, Track, Event, MidiError
from batch_event_ops import edit_events

class BatchEventTests(unittest.TestCase):
    def song(self):
        return Song(1, 480, [Track([Event(10,0xb0,b'\x07\x64'),Event(20,0xf0,b'\x43\x10'),Event(30,0x90,b'\x3c\x64')]),Track([])])
    def test_move_multiple(self):
        s=self.song(); self.assertEqual(edit_events(s,[(0,0),(0,1)],10),2)
        self.assertEqual([e.tick for e in s.tracks[0].events],[20,30,30])
    def test_copy_to_other_track(self):
        s=self.song(); edit_events(s,[(0,0),(0,1)],5,True,1)
        self.assertEqual(len(s.tracks[0].events),3)
        self.assertEqual([(e.tick,e.status) for e in s.tracks[1].events],[(15,0xb0),(25,0xf0)])
    def test_move_to_other_track(self):
        s=self.song(); edit_events(s,[(0,0)],0,False,1)
        self.assertEqual(len(s.tracks[0].events),2)
        self.assertEqual(len(s.tracks[1].events),1)
    def test_bad_index_atomic(self):
        s=self.song(); before=s.to_bytes()
        with self.assertRaises(MidiError): edit_events(s,[(0,0),(0,99)],10)
        self.assertEqual(s.to_bytes(),before); self.assertFalse(s.dirty)
    def test_negative_atomic(self):
        s=self.song()
        with self.assertRaises(MidiError): edit_events(s,[(0,0)],-11)
        self.assertFalse(s.dirty)
    def test_duplicate_rejected(self):
        with self.assertRaises(MidiError): edit_events(self.song(),[(0,0),(0,0)])
    def test_structural_event_rejected(self):
        s=self.song(); s.tracks[0].events.append(Event(100,0xff,b'',0x2f))
        with self.assertRaises(MidiError): edit_events(s,[(0,3)],5)
    def test_bool_delta_rejected(self):
        with self.assertRaises(MidiError): edit_events(self.song(),[(0,0)],True)
