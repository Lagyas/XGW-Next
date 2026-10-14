import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'editor'))
import unittest
from edit_history import EditHistory
from midi import Song,Track,Event

class HistoryTests(unittest.TestCase):
    def song(self, tick):
        return Song(1,480,[Track([Event(tick,0x90,b'\x3c\x40')])])
    def test_undo_redo(self):
        h=EditHistory(); a=self.song(10); h.checkpoint(a); b=self.song(20)
        a,ok=h.undo(b); self.assertTrue(ok); self.assertEqual(a.tracks[0].events[0].tick,10)
        b,ok=h.redo(a); self.assertTrue(ok); self.assertEqual(b.tracks[0].events[0].tick,20)
    def test_redo_invalidated(self):
        h=EditHistory(); h.checkpoint(self.song(1)); s,_=h.undo(self.song(2)); h.checkpoint(s)
        _,ok=h.redo(s); self.assertFalse(ok)
    def test_empty_noop(self):
        h=EditHistory(); s=self.song(1); result,ok=h.undo(s); self.assertIs(result,s); self.assertFalse(ok)
    def test_deep_copy(self):
        h=EditHistory(); s=self.song(1); h.checkpoint(s); s.tracks[0].events[0].tick=99
        old,_=h.undo(s); self.assertEqual(old.tracks[0].events[0].tick,1)
    def test_limit(self):
        h=EditHistory(2)
        for n in range(4): h.checkpoint(self.song(n))
        self.assertEqual(len(h.past),2)
    def test_invalid_limit(self):
        with self.assertRaises(ValueError): EditHistory(0)
