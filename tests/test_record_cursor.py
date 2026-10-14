import unittest
from types import SimpleNamespace
from unittest.mock import patch
from midi_recording import MidiRecorder


class RecordCursorTests(unittest.TestCase):
    def setUp(self):
        self.recorder = MidiRecorder()
        self.recorder._capture = SimpleNamespace(start_tick=480, division=480,
            bpm=120, _tempo_clock=None)
        self.recorder._started_at = 100.0

    def test_inactive_has_no_cursor(self):
        self.assertIsNone(self.recorder.current_tick(101))

    def test_fixed_tempo_clock(self):
        with patch.object(MidiRecorder, 'recording', new_callable=lambda: property(lambda _: True)):
            self.assertEqual(self.recorder.current_tick(101), 1440)

    def test_preroll_does_not_move_backward(self):
        with patch.object(MidiRecorder, 'recording', new_callable=lambda: property(lambda _: True)):
            self.assertEqual(self.recorder.current_tick(99), 480)

    def test_song_tempo_clock_is_used(self):
        self.recorder._capture._tempo_clock = SimpleNamespace(tick_at=lambda seconds: 480 + int(seconds * 100))
        with patch.object(MidiRecorder, 'recording', new_callable=lambda: property(lambda _: True)):
            self.assertEqual(self.recorder.current_tick(102), 680)

    def test_cursor_saturates_at_max_tick(self):
        with patch.object(MidiRecorder, 'recording', new_callable=lambda: property(lambda _: True)):
            self.assertEqual(self.recorder.current_tick(1e12), 0x0fffffff)


if __name__ == '__main__':
    unittest.main()
