import sys
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, Track, Event, MidiError
from midi_output import timed_messages, available_outputs

class MidiOutputTests(unittest.TestCase):
    def test_output_enumeration_uses_rtmidi(self):
        class FakeMido:
            def __init__(self):
                self.backend = None
            def set_backend(self, name):
                self.backend = name
            def get_output_names(self):
                return ["USB MIDI OUT"]
        fake = FakeMido()
        with patch.dict(sys.modules, {"mido": fake}):
            self.assertEqual(available_outputs(), ["USB MIDI OUT"])
        self.assertEqual(fake.backend, "mido.backends.rtmidi")

    def test_empty_output_list_is_valid(self):
        class FakeMido:
            def set_backend(self, name):
                pass
            def get_output_names(self):
                return []
        with patch.dict(sys.modules, {"mido": FakeMido()}):
            self.assertEqual(available_outputs(), [])

    def test_backend_failure_is_reported(self):
        class FakeMido:
            def set_backend(self, name):
                raise RuntimeError("driver unavailable")
        with patch.dict(sys.modules, {"mido": FakeMido()}):
            with self.assertRaisesRegex(MidiError, "driver unavailable"):
                available_outputs()

    def test_default_tempo(self):
        song = Song(0, 480, [Track([
            Event(0, 0x90, bytes((60, 100)), order=0),
            Event(480, 0x80, bytes((60, 0)), order=1)
        ])])
        self.assertEqual(list(timed_messages(song)),
                         [(0.0, bytes((0x90, 60, 100))), (0.5, bytes((0x80, 60, 0)))])

    def test_tempo_change(self):
        song = Song(1, 480, [
            Track([Event(480, 0xff, (1000000).to_bytes(3, "big"), 0x51, 0)]),
            Track([
                Event(0, 0x90, bytes((60, 100)), order=0),
                Event(960, 0x80, bytes((60, 0)), order=1),
            ])
        ])
        events = list(timed_messages(song))
        self.assertEqual(events[0][0], 0)
        self.assertAlmostEqual(events[1][0], 1.5)

    def test_sysex_not_sent(self):
        song = Song(0, 480, [Track([
            Event(0, 0xf0, b"\x43\x10\x4c", order=0),
            Event(0, 0x90, bytes((64, 90)), order=1)
        ])])
        self.assertEqual(len(list(timed_messages(song))), 1)

    def test_smpte_rejected(self):
        song = Song(0, 0xe728, [Track([])])
        with self.assertRaises(MidiError):
            list(timed_messages(song))

if __name__ == "__main__":
    unittest.main()
