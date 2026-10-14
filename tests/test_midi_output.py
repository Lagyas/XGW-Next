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

    def test_playback_from_middle_at_default_tempo(self):
        song = Song(0, 480, [Track([
            Event(0, 0x90, bytes((60, 100)), order=0),
            Event(480, 0x80, bytes((60, 0)), order=1),
            Event(960, 0x90, bytes((62, 100)), order=2),
            Event(1440, 0x80, bytes((62, 0)), order=3),
        ])])
        self.assertEqual(list(timed_messages(song, start_tick=960)), [
            (0.0, bytes((0x90, 62, 100))),
            (0.5, bytes((0x80, 62, 0))),
        ])

    def test_playback_from_middle_with_tempo_change(self):
        song = Song(1, 480, [
            Track([Event(480, 0xff, (1000000).to_bytes(3, "big"), 0x51, 0)]),
            Track([Event(960, 0x90, bytes((60, 100)), order=0),
                   Event(1440, 0x80, bytes((60, 0)), order=1)]),
        ])
        events = list(timed_messages(song, start_tick=720))
        self.assertAlmostEqual(events[0][0], 0.5)
        self.assertAlmostEqual(events[1][0], 1.5)

    def test_start_tick_validation(self):
        song = Song(0, 480, [Track([])])
        for invalid in (-1, 0x10000000, 1.5, True):
            with self.assertRaises(MidiError):
                list(timed_messages(song, start_tick=invalid))

    def test_chase_bank_program_and_controller(self):
        song = Song(0, 480, [Track([
            Event(0, 0xb0, bytes((0, 43)), order=0),
            Event(0, 0xb0, bytes((32, 2)), order=1),
            Event(0, 0xc0, bytes((17,)), order=2),
            Event(240, 0xb0, bytes((7, 90)), order=3),
            Event(480, 0x90, bytes((60, 100)), order=4),
        ])])
        events = list(timed_messages(song, start_tick=480))
        self.assertEqual([payload for _, payload in events], [
            bytes((0xb0, 0, 43)), bytes((0xb0, 32, 2)),
            bytes((0xc0, 17)), bytes((0xb0, 7, 90)),
            bytes((0x90, 60, 100))])
        self.assertTrue(all(t == 0 for t, _ in events))

    def test_chase_latest_values_and_respects_tracks(self):
        song = Song(1, 480, [
            Track([Event(0, 0xb0, bytes((7, 20))),
                   Event(240, 0xb0, bytes((7, 75)))]),
            Track([Event(0, 0xb1, bytes((7, 60))),
                   Event(480, 0x91, bytes((60, 100)))]),
        ])
        events = list(timed_messages(song, start_tick=480, enabled_tracks={1}))
        self.assertEqual(events, [(0.0, bytes((0xb1, 7, 60))),
                                  (0.0, bytes((0x91, 60, 100)))])

    def test_chase_can_be_disabled(self):
        song = Song(0, 480, [Track([
            Event(0, 0xc0, bytes((12,))),
            Event(480, 0x90, bytes((60, 100)))])])
        self.assertEqual(list(timed_messages(song, start_tick=480, chase=False)),
                         [(0.0, bytes((0x90, 60, 100)))])

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

class LoopTests(unittest.TestCase):
    def test_duration_follows_tempo_changes(self):
        from midi_output import loop_messages, tick_seconds
        song = Song(1, 480, [
            Track([Event(480, 0xff, (1000000).to_bytes(3, 'big'), 0x51)]),
            Track([Event(240, 0x90, b'\x3c\x64'),
                   Event(960, 0x80, b'\x3c\x00')])])
        self.assertAlmostEqual(tick_seconds(song, 960), 1.5)
        timeline, duration = loop_messages(song, 240, 960)
        self.assertAlmostEqual(duration, 1.25)
        self.assertEqual(timeline[0], (0, b'\x90\x3c\x64'))
        self.assertEqual(len(timeline), 1)  # End boundary is exclusive.

    def test_loop_chases_state(self):
        from midi_output import loop_messages
        song = Song(0, 480, [Track([
            Event(0, 0xc0, b'\x0c'),
            Event(480, 0x90, b'\x3c\x40'),
            Event(960, 0x80, b'\x3c\x00')])])
        timeline, duration = loop_messages(song, 480, 960)
        self.assertEqual(timeline, [(0, b'\xc0\x0c'), (0, b'\x90\x3c\x40')])
        self.assertAlmostEqual(duration, .5)

    def test_invalid_loop(self):
        from midi_output import loop_messages
        song = Song(0, 480, [Track([])])
        for start, end in ((480, 480), (500, 100), (-1, 100), (0, True)):
            with self.assertRaises(MidiError):
                loop_messages(song, start, end)
