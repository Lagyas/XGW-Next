import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import MidiError
from midi2_ump import UmpPacket, midi2_note_on, midi2_note_off, midi2_control_change, unpack_ump_stream

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

    def test_note_off_zero_release_velocity(self):
        packet = midi2_note_off(1, 2, 64, 0)
        fields = packet.midi2_channel_voice()
        self.assertEqual(fields["status"], 8)
        self.assertEqual(fields["data32"] >> 16, 0)

    def test_32bit_control_change(self):
        packet = midi2_control_change(0, 15, 74, 0xffffffff)
        fields = packet.midi2_channel_voice()
        self.assertEqual(fields["status"], 11)
        self.assertEqual(fields["index"], 74)
        self.assertEqual(fields["data32"], 0xffffffff)

    def test_ump_stream_with_mixed_packet_sizes(self):
        one = UmpPacket((0x20903c64,))
        two = midi2_note_on(1, 0, 60, 30000)
        three = midi2_control_change(1, 0, 7, 0x12345678)
        data = one.to_bytes() + two.to_bytes() + three.to_bytes()
        self.assertEqual(unpack_ump_stream(data), [one, two, three])
        with self.assertRaises(MidiError):
            unpack_ump_stream(data[:-4])

    def test_invalid_note_fields(self):
        for args in ((0, 0, 60, 0), (16, 0, 60, 100), (0, 0, 128, 100)):
            with self.assertRaises(MidiError):
                midi2_note_on(*args)

if __name__ == "__main__":
    unittest.main()
