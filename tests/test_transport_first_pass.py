"""Regression: cursor-to-R first pass must not be replaced by L-to-R."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from midi_output import MidiPlayer

class FirstPassTests(unittest.TestCase):
    def test_first_pass_cursor_inside_loop(self):
        self.check_pass(250, 250)

    def test_first_pass_cursor_before_left_locator(self):
        self.check_pass(50, 50)

    def test_first_pass_at_left_locator(self):
        self.check_pass(100, 100)

    def check_pass(self, cursor, expected):
        song = SimpleNamespace(tracks=[], division=480)
        player = MidiPlayer()
        with patch('midi_output.tick_seconds', side_effect=lambda song, tick: tick / 100), \
             patch('midi_output.loop_messages', return_value=([(0, b'\x90\x3c\x40')], 2.0)), \
             patch('midi_output.timed_messages', return_value=[(0, b'\x90\x3d\x40')]) as events, \
             patch('midi_output.threading.Thread') as thread:
            player.play(song, 'test-port', start_tick=cursor, loop_start=100, loop_end=300)
            self.assertEqual(events.call_args.kwargs['start_tick'], expected)
            args = thread.call_args.kwargs['args']
            self.assertEqual(args[0], [(0, b'\x90\x3d\x40')])
            self.assertEqual(args[3], [(0, b'\x90\x3c\x40')])
            self.assertAlmostEqual(args[4], (300-cursor)/100)
