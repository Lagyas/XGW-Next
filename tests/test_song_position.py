import unittest
from midi import Event, MidiError, Song, Track
from song_position import tick_to_bbt, format_bbt


class SongPositionTests(unittest.TestCase):
    def test_four_four(self):
        song = Song(1, 480, [Track()])
        self.assertEqual(tick_to_bbt(song, 0), (1, 1, 0))
        self.assertEqual(tick_to_bbt(song, 479), (1, 1, 479))
        self.assertEqual(tick_to_bbt(song, 480), (1, 2, 0))
        self.assertEqual(format_bbt(song, 1920), '0002:01:000')

    def test_three_eight(self):
        song = Song(1, 480, [Track([Event(0, 0xff, b'\x03\x03\x18\x08', meta_type=0x58)])])
        self.assertEqual(tick_to_bbt(song, 240), (1, 2, 0))
        self.assertEqual(tick_to_bbt(song, 720), (2, 1, 0))

    def test_mid_bar_meter_change(self):
        song = Song(1, 480, [Track([Event(960, 0xff, b'\x03\x02\x18\x08', meta_type=0x58)])])
        self.assertEqual(tick_to_bbt(song, 959), (1, 2, 479))
        self.assertEqual(tick_to_bbt(song, 960), (2, 1, 0))
        self.assertEqual(tick_to_bbt(song, 2400), (3, 1, 0))

    def test_invalid_ticks(self):
        song = Song(1, 480, [Track()])
        for tick in (-1, 1.5, True):
            with self.assertRaises(MidiError):
                tick_to_bbt(song, tick)
