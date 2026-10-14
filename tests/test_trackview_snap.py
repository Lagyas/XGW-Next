import unittest
from sequencer_view import timeline_snap_tick, clip_drag_delta
from midi import MidiError

class TrackViewSnapTests(unittest.TestCase):
    def test_quarter(self):
        self.assertEqual(timeline_snap_tick(281, 480, '1/4'), 480)
    def test_sixteenth(self):
        self.assertEqual(timeline_snap_tick(181, 480, '1/16'), 240)
    def test_off(self):
        self.assertEqual(timeline_snap_tick(181, 480, 'Off'), 181)
    def test_negative_clamped(self):
        self.assertEqual(timeline_snap_tick(-10, 480, 'Off'), 0)
    def test_clip_delta(self):
        self.assertEqual(clip_drag_delta(-170, 480, '1/8'), -240)
    def test_clip_delta_off(self):
        self.assertEqual(clip_drag_delta(17.6, 480, 'Off'), 18)
    def test_invalid_option(self):
        with self.assertRaises(MidiError):
            timeline_snap_tick(120, 480, 'bogus')
