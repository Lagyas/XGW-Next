"""Pause/resume output lifecycle regression tests (no MIDI hardware required)."""
import sys
import threading
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi_output import MidiPlayer

class PauseOutputTests(unittest.TestCase):
    def test_wait_without_worker(self):
        self.assertTrue(MidiPlayer().wait_stopped(0))

    def test_wait_completed_worker(self):
        player = MidiPlayer()
        player._thread = threading.Thread(target=lambda: None)
        player._thread.start()
        self.assertTrue(player.wait_stopped(1))

    def test_wait_busy_worker(self):
        gate = threading.Event()
        started = threading.Event()
        def worker():
            started.set()
            gate.wait(2)
        player = MidiPlayer()
        player._thread = threading.Thread(target=worker)
        player._thread.start()
        try:
            self.assertTrue(started.wait(1))
            self.assertFalse(player.wait_stopped(0))
        finally:
            gate.set()
            player._thread.join(2)

    def test_stop_wakes_output(self):
        player = MidiPlayer()
        player.stop()
        self.assertTrue(player._stop.is_set())
        self.assertTrue(player._wake.is_set())

if __name__ == '__main__':
    unittest.main()
