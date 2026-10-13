import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import MidiError
from xg_parts import XGParts
from xg_sysex import decode_parameter_change

class XGPartTests(unittest.TestCase):
    def test_part_volume_address(self):
        model = XGParts()
        model.set(3, "volume", 87)
        message = model.message(3, "volume")
        self.assertEqual(message, bytes.fromhex("F0 43 10 4C 08 03 0B 57 F7"))
        self.assertEqual(decode_parameter_change(message)["data"], b"\x57")

    def test_roundtrip_model(self):
        a, b = XGParts(), XGParts()
        a.set(5, "pan", 12)
        self.assertTrue(b.apply_sysex(a.message(5, "pan")))
        self.assertEqual(b.parts[5].pan, 12)

    def test_reject_invalid_value(self):
        model = XGParts()
        with self.assertRaises(MidiError):
            model.set(0, "volume", 128)

    def test_non_part_message_ignored(self):
        model = XGParts()
        self.assertFalse(model.apply_sysex(bytes.fromhex("F0 43 10 4C 00 00 7E 00 F7")))

if __name__ == "__main__":
    unittest.main()
