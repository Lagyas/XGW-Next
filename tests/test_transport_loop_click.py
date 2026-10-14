"""Metronome first pass and repeat schedule must use different origins."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track
from midi_output import MidiPlayer

class LoopClickTests(unittest.TestCase):
    def check(self, cursor, expected_first):
        song = Song(0, 480, [Track([])])
        with patch('midi_output.threading.Thread') as worker:
            MidiPlayer().play(song, 'mock-port', start_tick=cursor,
                              loop_start=480, loop_end=1920, metronome=True)
        args = worker.call_args.kwargs['args']
        first_on = [(round(t, 3), msg[1]) for t, msg in args[0] if msg[0] == 0x99]
        repeat_on = [(round(t, 3), msg[1]) for t, msg in args[3] if msg[0] == 0x99]
        self.assertEqual(first_on, expected_first)
        self.assertEqual(repeat_on, [(0, 77), (0.5, 77), (1, 77)])
        self.assertAlmostEqual(args[4], (1920-cursor)/960)
        self.assertAlmostEqual(args[2], 1.5)

    def test_cursor_inside_loop(self):
        self.check(960, [(0, 77), (0.5, 77)])

    def test_cursor_at_left(self):
        self.check(480, [(0, 77), (0.5, 77), (1, 77)])

    def test_cursor_before_left(self):
        self.check(0, [(0, 76), (0.5, 77), (1, 77), (1.5, 77)])

if __name__ == '__main__':
    unittest.main()
