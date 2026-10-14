import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from xg_mixer_bridge import mapped_mixer_snapshot, write_xg_part_changes
from mixer_ops import set_channel_values

class MappingTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [Track([Event(0, 0xff, b'', 0x2f, 0)])])
        write_xg_part_changes(self.song, 0, 4, {'volume': 72}, tick=12, device=2)
        set_channel_values(self.song, 0, 7, {'Pan': 23}, 10)

    def test_explicit_nonidentity_mapping(self):
        values, sources = mapped_mixer_snapshot(self.song, {7: (4, 2)}, 15)[7]
        self.assertEqual(values['Volume'], 72)
        self.assertEqual(sources['Volume'], 'XG SysEx')
        self.assertEqual(values['Pan'], 23)

    def test_wrong_device_does_not_leak(self):
        self.assertEqual(mapped_mixer_snapshot(self.song, {7: (4, 0)}, 15)[7][0]['Volume'], 100)

    def test_before_automation(self):
        self.assertEqual(mapped_mixer_snapshot(self.song, {7: (4, 2)}, 11)[7][0]['Volume'], 100)

    def test_invalid_mappings(self):
        for mapping in ({}, {True: (4, 2)}, {7: (4, True)}, {7: (17, 0)}, {7: (4,)}, {7: '4,2'}):
            with self.subTest(mapping=mapping), self.assertRaises(MidiError):
                mapped_mixer_snapshot(self.song, mapping, 15)

    def test_invalid_tick(self):
        with self.assertRaises(MidiError):
            mapped_mixer_snapshot(self.song, {7: (4, 2)}, True)
