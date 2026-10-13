import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Event, MidiError
from event_fields import event_fields, encode_fields

class EventFieldsTests(unittest.TestCase):
    def test_note_fields(self):
        event = Event(0, 0x90, bytes((60, 100)))
        self.assertEqual([field[0] for field in event_fields(event)], ["Note", "Velocity"])
        self.assertEqual(encode_fields(event, [65, 80]), bytes((65, 80)))

    def test_control_change(self):
        event = Event(0, 0xb0, bytes((7, 100)))
        self.assertEqual(encode_fields(event, [10, 64]), bytes((10, 64)))

    def test_program_change(self):
        event = Event(0, 0xc0, bytes((12,)))
        self.assertEqual(encode_fields(event, [127]), bytes((127,)))

    def test_pitch_bend_center_and_extremes(self):
        event = Event(0, 0xe0, bytes((0, 64)))
        self.assertEqual(event_fields(event)[0][1], 8192)
        for value in (0, 8192, 16383):
            encoded = encode_fields(event, [value])
            self.assertEqual(encoded[0] | (encoded[1] << 7), value)

    def test_invalid_values_rejected(self):
        event = Event(0, 0x90, bytes((60, 100)))
        for values in ([128, 100], [60, -1], [60], [60, 100.0]):
            with self.assertRaises(MidiError):
                encode_fields(event, values)

    def test_polyphonic_aftertouch(self):
        event = Event(0, 0xa2, bytes((60, 30)))
        self.assertEqual([f[0] for f in event_fields(event)], ["Note", "Pressure"])
        self.assertEqual(encode_fields(event, [64, 99]), bytes((64, 99)))

    def test_channel_aftertouch(self):
        event = Event(0, 0xd1, bytes((35,)))
        self.assertEqual(event_fields(event)[0][1], 35)
        self.assertEqual(encode_fields(event, [100]), bytes((100,)))

    def test_meta_not_supported(self):
        with self.assertRaises(MidiError):
            event_fields(Event(0, 0xff, b"", 0x2f))

if __name__ == "__main__":
    unittest.main()
