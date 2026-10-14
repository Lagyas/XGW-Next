import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from midi_output import metronome_messages, count_in_messages

class MetronomeTests(unittest.TestCase):
    def test_four_four_accents_and_note_off(self):
        song = Song(0, 480, [Track([])])
        clicks = metronome_messages(song, 0, 1920)
        ons = [(t, msg[1]) for t, msg in clicks if msg[0] == 0x99]
        self.assertEqual(ons, [(0, 76), (.5, 77), (1., 77), (1.5, 77)])
        self.assertEqual(sum(msg[0] == 0x89 for _, msg in clicks), 4)

    def test_tempo_change(self):
        song = Song(0, 480, [Track([Event(480, 0xff, (1000000).to_bytes(3, 'big'), 0x51)])])
        ons = [t for t, msg in metronome_messages(song, 0, 1440) if msg[0] == 0x99]
        self.assertEqual(ons, [0, .5, 1.5])

    def test_meter_change_restarts_accent(self):
        song = Song(0, 480, [Track([Event(960, 0xff, bytes((3, 2, 24, 8)), 0x58)])])
        ons = [(round(t, 2), msg[1]) for t, msg in metronome_messages(song, 0, 2400) if msg[0] == 0x99]
        self.assertEqual(ons, [(0, 76), (.5, 77), (1, 76), (1.5, 77), (2, 77)])

    def test_region_mid_bar(self):
        song = Song(0, 480, [Track([])])
        ons = [t for t, msg in metronome_messages(song, 600, 1500) if msg[0] == 0x99]
        self.assertEqual(ons, [.375, .875])

    def test_invalid_settings(self):
        song = Song(0, 480, [Track([])])
        for args in ((0, 0), (480, 0), (-1, 480)):
            with self.assertRaises(MidiError):
                metronome_messages(song, *args)
        with self.assertRaises(MidiError):
            metronome_messages(song, 0, 480, channel=16)

if __name__ == '__main__':
    unittest.main()

class CountInTests(unittest.TestCase):
    def test_one_bar_4_4(self):
        song = Song(0, 480, [Track([])])
        clicks, duration = count_in_messages(song, 0, 1)
        self.assertEqual(duration, 2.0)
        self.assertEqual([(round(t, 2), msg[1]) for t, msg in clicks if msg[0] == 0x99],
                         [(-2, 76), (-1.5, 77), (-1, 77), (-.5, 77)])
        self.assertTrue(all(t < 0 for t, _ in clicks))

    def test_tempo_and_meter_at_start(self):
        song = Song(0, 480, [Track([
            Event(0, 0xff, bytes((3, 2, 24, 8)), 0x58),
            Event(480, 0xff, (1000000).to_bytes(3, 'big'), 0x51)])])
        clicks, duration = count_in_messages(song, 960, 2)
        self.assertEqual(duration, 6.0)
        self.assertEqual(len([m for _, m in clicks if m[0] == 0x99]), 6)

    def test_zero_and_invalid(self):
        song = Song(0, 480, [Track([])])
        self.assertEqual(count_in_messages(song, 0, 0), ([], 0.0))
        for value in (-1, 9, 1.5, True):
            with self.assertRaises(MidiError):
                count_in_messages(song, 0, value)
