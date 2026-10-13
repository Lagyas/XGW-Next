import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, MidiError, Event, Track

class TestMidi(unittest.TestCase):
    def test_basic_edit(self):
        s = Song(1, 480, [Track([
            Event(0, 0x90, b"\x3c\x64", order=0),
            Event(480, 0x80, b"\x3c\x00", order=1),
            Event(480, 0xff, b"", 0x2f, 2)
        ])])
        data = s.to_bytes()
        parsed = Song.from_bytes(data)
        self.assertEqual(parsed.to_bytes(), data)
        self.assertEqual(parsed.transpose(0, 2), 2)
        after = Song.from_bytes(parsed.to_bytes())
        self.assertEqual(after.tracks[0].events[0].data, b"\x3e\x64")
        self.assertEqual(after.tracks[0].events[1].data, b"\x3e\x00")

    def test_preserve_meta_sysex(self):
        s = Song(0, 96, [Track([
            Event(0, 0xf0, b"\x43\x10\x4c\x00", order=0),
            Event(0, 0xff, b"abc", 0x7f, 1),
            Event(0, 0xff, b"", 0x2f, 2)
        ])])
        b = s.to_bytes()
        t = Song.from_bytes(b)
        self.assertEqual(t.to_bytes(), b)
        t.dirty = True
        self.assertEqual(Song.from_bytes(t.to_bytes()).tracks[0].events[1].data, b"abc")

    def test_overflow_rejected(self):
        s = Song(0, 480, [Track([Event(0, 0x90, b"\x7f\x40")])])
        t = Song.from_bytes(s.to_bytes())
        with self.assertRaises(MidiError):
            t.transpose(0, 1)

if __name__ == "__main__":
    unittest.main()
