import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import unittest
from midi import Song, Track, Event, MidiError
from clip_boundaries import legato_clip_notes
from note_ops import paired_notes


def sample():
    return Song(1, 480, [Track([
        Event(0, 0x90, b'\x3c\x64', order=0),
        Event(100, 0x80, b'\x3c\x00', order=1),
        Event(200, 0x90, b'\x3e\x64', order=2),
        Event(300, 0x80, b'\x3e\x00', order=3),
        Event(150, 0xb0, b'\x07\x50', order=4),
        Event(400, 0x90, b'\x40\x64', order=5),
        Event(450, 0x80, b'\x40\x00', order=6),
    ])])

class LegatoTests(unittest.TestCase):
    def test_extends_notes_to_next_onset(self):
        s=sample(); self.assertEqual(legato_clip_notes(s,0,0),2)
        self.assertEqual(sorted((s.tracks[0].events[a].tick,s.tracks[0].events[b].tick) for a,b in paired_notes(s.tracks[0])),[(0,200),(200,400),(400,450)])
        self.assertEqual(s.tracks[0].events[4].tick,150)
    def test_gap(self):
        s=sample(); self.assertEqual(legato_clip_notes(s,0,0,20),2)
        self.assertEqual(s.tracks[0].events[1].tick,180)
    def test_same_pitch_only(self):
        s=sample(); self.assertEqual(legato_clip_notes(s,0,0,same_pitch=True),0)
        self.assertFalse(s.dirty)
    def test_invalid_atomic(self):
        s=sample(); before=s.to_bytes()
        with self.assertRaises(MidiError): legato_clip_notes(s,0,0,-1)
        self.assertEqual(s.to_bytes(),before)
    def test_idempotent(self):
        s=sample(); legato_clip_notes(s,0,0)
        self.assertEqual(legato_clip_notes(s,0,0),0)
    def test_roundtrip(self):
        s=sample(); legato_clip_notes(s,0,0)
        reloaded=Song.from_bytes(s.to_bytes())
        self.assertEqual(len(paired_notes(reloaded.tracks[0])),3)
