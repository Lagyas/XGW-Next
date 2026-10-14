import unittest
from midi import Event, MidiError, Song, Track
from song_position import bbt_to_tick, parse_bbt, tick_to_bbt


class TransportBbtInputTests(unittest.TestCase):
    def test_four_four(self):
        song = Song(1, 480, [Track()])
        self.assertEqual(parse_bbt(song, '0012:03:000'), 22080)
        self.assertEqual(bbt_to_tick(song, 2, 1, 0), 1920)

    def test_three_eight(self):
        song = Song(1, 480, [Track([Event(0, 0xff, b'\x03\x03\x18\x08', meta_type=0x58)])])
        self.assertEqual(parse_bbt(song, '0002:02:000'), 960)
        with self.assertRaises(MidiError):
            parse_bbt(song, '0002:04:000')

    def test_meter_change_mid_bar(self):
        song = Song(1, 480, [Track([Event(960, 0xff, b'\x03\x02\x18\x08', meta_type=0x58)])])
        self.assertEqual(parse_bbt(song, '0002:01:000'), 960)
        self.assertEqual(tick_to_bbt(song, parse_bbt(song, '0003:01:000')), (3, 1, 0))
        with self.assertRaises(MidiError):
            parse_bbt(song, '0001:03:000')

    def test_invalid_input(self):
        song = Song(1, 480, [Track()])
        for value in ('abc', '1:2', '0:1:0', '1:0:0', '1:1:-1', '1:1:480'):
            with self.subTest(value=value), self.assertRaises(MidiError):
                parse_bbt(song, value)
