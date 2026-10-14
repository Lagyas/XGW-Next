import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Event, MidiError
from midi2_bridge import (midi1_event_to_midi2, scale_7_to_16,
                          scale_7_to_32, scale_14_to_32)


class Midi2BridgeTests(unittest.TestCase):
    def test_scaling_endpoints(self):
        self.assertEqual((scale_7_to_16(0), scale_7_to_16(127)), (0, 65535))
        self.assertEqual((scale_7_to_32(0), scale_7_to_32(127)), (0, 0xffffffff))
        self.assertEqual((scale_14_to_32(0), scale_14_to_32(16383)), (0, 0xffffffff))
        self.assertEqual(scale_14_to_32(8192), 0x80020008)

    def test_note_on_and_off(self):
        on = midi1_event_to_midi2(Event(0, 0x92, bytes((60, 100))), 3)
        self.assertEqual((on.group, on.midi2_channel_voice()["channel"]), (3, 2))
        self.assertEqual(on.midi2_channel_voice()["status"], 9)
        self.assertEqual(on.midi2_channel_voice()["data32"] >> 16, scale_7_to_16(100))
        off = midi1_event_to_midi2(Event(100, 0x92, bytes((60, 0))))
        self.assertEqual(off.midi2_channel_voice()["status"], 8)

    def test_controller_and_pitch_bend(self):
        cc = midi1_event_to_midi2(Event(0, 0xb0, bytes((74, 127))))
        self.assertEqual(cc.midi2_channel_voice()["data32"], 0xffffffff)
        bend = midi1_event_to_midi2(Event(0, 0xe1, bytes((0, 64))))
        self.assertEqual(bend.midi2_channel_voice()["data32"], scale_14_to_32(8192))

    def test_remaining_channel_voice_messages(self):
        poly = midi1_event_to_midi2(Event(0, 0xa0, bytes((60, 64))))
        self.assertEqual(poly.midi2_channel_voice()["status"], 10)
        self.assertEqual(poly.midi2_channel_voice()["data32"], scale_7_to_32(64))
        pressure = midi1_event_to_midi2(Event(0, 0xd0, bytes((100,))))
        self.assertEqual(pressure.midi2_channel_voice()["status"], 13)
        self.assertEqual(pressure.midi2_channel_voice()["data32"], scale_7_to_32(100))
        program = midi1_event_to_midi2(Event(0, 0xc0, bytes((127,))))
        self.assertEqual(program.midi2_channel_voice()["status"], 12)
        self.assertEqual(program.midi2_channel_voice()["data32"], 127 << 24)

    def test_unsupported_is_explicit(self):
        for event in (Event(0, 0xff, b"", 0x2f),
                      Event(0, 0x90, b"\x40")):
            with self.assertRaises(MidiError):
                midi1_event_to_midi2(event)
        with self.assertRaises(MidiError):
            midi1_event_to_midi2(Event(0, 0x90, b"\x40\x7f"), 16)

    def test_bad_scaling(self):
        for f, value in ((scale_7_to_16, 128), (scale_7_to_32, -1),
                         (scale_14_to_32, 16384), (scale_7_to_16, True)):
            with self.assertRaises(MidiError):
                f(value)


if __name__ == "__main__":
    unittest.main()
