import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from mixer_ops import set_channel_values
from xg_mixer_bridge import combined_part_values, write_xg_part_changes

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [Track([Event(0, 0xff, b'', 0x2f, 0)])])

    def test_cc_and_xg_latest_by_tick(self):
        set_channel_values(self.song, 0, 1, {'Volume': 45}, 10)
        write_xg_part_changes(self.song, 0, 1, {'volume': 82}, 20)
        self.assertEqual(combined_part_values(self.song, 1, 1, 15)[0]['Volume'], 45)
        values, sources = combined_part_values(self.song, 1, 1, 25)
        self.assertEqual((values['Volume'], sources['Volume']), (82, 'XG SysEx'))
        set_channel_values(self.song, 0, 1, {'Volume': 60}, 30)
        self.assertEqual(combined_part_values(self.song, 1, 1, 30)[0]['Volume'], 60)

    def test_part_isolation(self):
        write_xg_part_changes(self.song, 0, 2, {'pan': 30})
        self.assertEqual(combined_part_values(self.song, 1, 1)[0]['Pan'], 64)
        self.assertEqual(combined_part_values(self.song, 2, 2)[0]['Pan'], 30)

    def test_device_isolation(self):
        write_xg_part_changes(self.song, 0, 1, {'pan': 22}, device=3)
        self.assertEqual(combined_part_values(self.song, 1, 1)[0]['Pan'], 64)
        self.assertEqual(combined_part_values(self.song, 1, 1, device=3)[0]['Pan'], 22)

    def test_replace_and_roundtrip(self):
        write_xg_part_changes(self.song, 0, 1, {'volume': 12})
        write_xg_part_changes(self.song, 0, 1, {'volume': 99})
        self.assertEqual(sum(e.status == 0xf0 for e in self.song.tracks[0].events), 1)
        parsed = Song.from_bytes(self.song.to_bytes())
        self.assertEqual(combined_part_values(parsed, 1, 1)[0]['Volume'], 99)

    def test_validation_is_atomic(self):
        before = self.song.to_bytes()
        with self.assertRaises(MidiError):
            write_xg_part_changes(self.song, 0, 1, {'volume': 30, 'pan': 128})
        self.assertEqual(self.song.to_bytes(), before)

    def test_boolean_inputs_rejected(self):
        with self.assertRaises(MidiError):
            combined_part_values(self.song, True, 1)
        with self.assertRaises(MidiError):
            write_xg_part_changes(self.song, 0, 1, {'volume': True})

    def test_other_sysex_preserved(self):
        write_xg_part_changes(self.song, 0, 1, {'volume': 12}, device=0)
        write_xg_part_changes(self.song, 0, 1, {'volume': 33}, device=1)
        write_xg_part_changes(self.song, 0, 1, {'volume': 44}, device=0)
        self.assertEqual(sum(e.status == 0xf0 for e in self.song.tracks[0].events), 2)
        self.assertEqual(combined_part_values(self.song, 1, 1, device=1)[0]['Volume'], 33)
