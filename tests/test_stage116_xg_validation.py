import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import MidiError
from xg_parts import XGParts
from xg_sysex import parameter_change, decode_parameter_change

class Stage116XgValidation(unittest.TestCase):
    def test_boolean_is_not_a_part_index(self):
        parts = XGParts()
        for part in (True, False, 16, -1):
            with self.subTest(part=part), self.assertRaises(MidiError):
                parts.set(part, 'volume', 50)
            with self.subTest(part=part), self.assertRaises(MidiError):
                parts.message(part, 'volume')
    def test_boolean_is_not_a_parameter_value(self):
        with self.assertRaises(MidiError):
            XGParts().set(0, 'volume', True)
    def test_valid_xg_parameter_change_roundtrip(self):
        raw = parameter_change((8, 0, 11), (100,), 0)
        decoded = decode_parameter_change(raw)
        self.assertEqual(decoded['address'], (8, 0, 11))
        self.assertEqual(decoded['data'], b'\x64')
    def test_boolean_byte_rejected(self):
        with self.assertRaises(MidiError):
            parameter_change((8, 0, 11), (True,))
