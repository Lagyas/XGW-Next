import unittest
from midi import MidiError
from transport_ops import playback_region, seek_position, tick_value, MAX_TICK

class TransportRegionTests(unittest.TestCase):
    def test_normal_playback_ignores_invalid_inactive_locators(self):
        self.assertEqual(playback_region('120', False, 'bad', '-1'), (120, None, None))

    def test_valid_loop(self):
        self.assertEqual(playback_region('240', True, '120', '480'), (240, 120, 480))

    def test_start_before_loop_is_allowed(self):
        self.assertEqual(playback_region('0', True, '120', '480'), (0, 120, 480))

    def test_invalid_ranges(self):
        for left, right in [('10', '10'), ('20', '10'), ('-1', '10'), ('0', 'oops')]:
            with self.subTest(left=left, right=right), self.assertRaises(MidiError):
                playback_region('0', True, left, right)

    def test_start_after_right_is_rejected(self):
        with self.assertRaises(MidiError):
            playback_region('480', True, '0', '480')

    def test_tick_validation(self):
        for value in (-1, MAX_TICK + 1, True, '1.5', '', None):
            with self.subTest(value=value), self.assertRaises(MidiError):
                tick_value(value)
        self.assertEqual(tick_value(str(MAX_TICK)), MAX_TICK)


class SeekPositionTests(unittest.TestCase):
    def test_seek_without_loop(self):
        self.assertEqual(seek_position('960', False, 'bad', 'bad'), 960)

    def test_seek_within_loop(self):
        self.assertEqual(seek_position(240, True, 120, 480), 240)

    def test_seek_before_left_first_leg(self):
        self.assertEqual(seek_position(0, True, 120, 480), 0)

    def test_seek_at_right_rejected(self):
        with self.assertRaises(MidiError):
            seek_position(480, True, 120, 480)

    def test_invalid_seek_does_not_silently_clamp(self):
        with self.assertRaises(MidiError):
            seek_position(-1)
