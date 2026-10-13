import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, Track, Event
from xg_voices import GM_NAMES, voice_name, voice_label, matching_voices
from voice_setup import insert_voice_setup

class VoiceCatalogTests(unittest.TestCase):
    def test_gm_count_and_names(self):
        self.assertEqual(len(GM_NAMES), 128)
        self.assertEqual(voice_name(0, 0, 0), "Acoustic Grand Piano")
        self.assertEqual(voice_name(0, 0, 127), "Gunshot")

    def test_known_variation(self):
        self.assertEqual(voice_name(0, 40, 0), "Piano Strings")
        self.assertIsNone(voice_name(0, 127, 0))
        self.assertIn("Unknown", voice_label(0, 127, 0))

    def test_search(self):
        self.assertTrue(any(p == 0 and lsb == 40 for _, lsb, p, _ in matching_voices("piano strings")))

    def test_song_voice_setup_roundtrip(self):
        song = Song(0, 480, [Track([
            Event(0, 0x90, bytes((60, 100)), order=0),
            Event(480, 0x80, bytes((60, 0)), order=1),
            Event(480, 0xff, b"", 0x2f, 2)
        ])])
        insert_voice_setup(song, 0, 1, 0, 40, 0)
        parsed = Song.from_bytes(song.to_bytes())
        zero = [e for e in parsed.tracks[0].events if e.tick == 0]
        self.assertEqual([e.status for e in zero[:3]], [0xb0, 0xb0, 0xc0])
        self.assertEqual([e.data for e in zero[:3]], [b"\x00\x00", b"\x20\x28", b"\x00"])

if __name__ == "__main__":
    unittest.main()
