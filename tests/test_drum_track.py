import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Event, Track, Song
from xg_drums import kit_name, GM_DRUM_NOTES
from xg_voices import voice_name, matching_voices
from track_voice import channel_voice_at, used_channels

class DrumAndTrackTests(unittest.TestCase):
    def test_drum_banks(self):
        self.assertEqual(kit_name(127, 0, 0), "Standard Kit 1")
        self.assertEqual(kit_name(127, 0, 32), "Jazz Kit")
        self.assertEqual(kit_name(126, 0, 1), "SFX Kit 2")
        self.assertIsNone(kit_name(127, 1, 0))
        self.assertEqual(GM_DRUM_NOTES[38], "Acoustic Snare")
        self.assertEqual(voice_name(127, 0, 40), "Brush Kit")
        self.assertTrue(any(msb == 127 for msb, _, _, _ in matching_voices("jazz kit")))

    def test_bank_commits_only_on_program_change(self):
        s = Song(0, 480, [Track([
            Event(0, 0xb0, bytes((0, 127)), order=0),
            Event(0, 0xb0, bytes((32, 0)), order=1),
            Event(120, 0xc0, bytes((32,)), order=2),
            Event(240, 0xb0, bytes((0, 0)), order=3),
            Event(300, 0x90, bytes((38, 100)), order=4),
        ])])
        self.assertFalse(channel_voice_at(s, 0, 1, 0).has_program_change)
        self.assertEqual(channel_voice_at(s, 0, 1, 120).msb, 127)
        self.assertEqual(channel_voice_at(s, 0, 1, 300).msb, 127)
        self.assertEqual(used_channels(s, 0), [1])

if __name__ == "__main__":
    unittest.main()
