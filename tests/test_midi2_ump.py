import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import MidiError
from midi2_ump import UmpPacket, midi2_note_on

class UmpTests(unittest.TestCase):
    def test_midi2_note_on_preserves_16bit_velocity(self):
        packet = midi2_note_on(2, 3, 60, 50000)
        self.assertEqual(packet.message_type, 4)
        self.assertEqual(packet.group, 2)
        self.assertEqual(packet.midi2_channel_voice()["channel"], 3)
        self.assertEqual(packet.midi2_channel_voice()["index"], 60)
        self.assertEqual(packet.midi2_channel_voice()["data32"] >> 16, 50000)

    def test_round_trip_bytes(self):
        packet = midi2_note_on(15, 15, 127, 65535, 1, 1234)
        self.assertEqual(UmpPacket.from_bytes(packet.to_bytes()), packet)

    def test_invalid_word_count(self):
        with self.assertRaises(MidiError):
            UmpPacket((0x40903c00,))
        with self.assertRaises(MidiError):
            UmpPacket.from_bytes(b"abc")

    def test_midi1_packet_is_distinct(self):
        packet = UmpPacket((0x20903c64,))
        self.assertEqual(packet.message_type, 2)
        with self.assertRaises(MidiError):
            packet.midi2_channel_voice()

    def test_invalid_note_fields(self):
        for args in ((0, 0, 60, 0), (16, 0, 60, 100), (0, 0, 128, 100)):
            with self.assertRaises(MidiError):
                midi2_note_on(*args)

if __name__ == "__main__":
    unittest.main()
