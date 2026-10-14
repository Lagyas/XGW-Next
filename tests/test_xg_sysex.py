import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, Track, Event, MidiError
from xg_sysex import (system_on, parameter_change, decode_parameter_change,
                       is_xg_system_on, smf_sysex_to_wire)
from midi_output import timed_messages

class XGSysexTests(unittest.TestCase):
    def test_system_on(self):
        raw = bytes.fromhex("F0 43 10 4C 00 00 7E 00 F7")
        self.assertEqual(system_on(), raw)
        self.assertTrue(is_xg_system_on(raw))
        self.assertEqual(decode_parameter_change(raw)["device"], 0)

    def test_parameter_change(self):
        raw = parameter_change((0x08, 0x00, 0x11), (0x40,), device=2)
        self.assertEqual(raw, bytes.fromhex("F0 43 12 4C 08 00 11 40 F7"))
        self.assertEqual(decode_parameter_change(raw)["data"], b"\x40")

    def test_invalid_data(self):
        with self.assertRaises(MidiError):
            parameter_change((0, 0, 0), (128,))

    def test_invalid_parameter_types_are_rejected(self):
        for address, data, device in [((0, 0, 0), (True,), 0),
                                      ((0, 0, 0), (1,), True),
                                      ((0, 0, 0), (1,), 1.0),
                                      (None, (1,), 0),
                                      ((0, 0, 0), None, 0)]:
            with self.subTest(address=address, data=data, device=device):
                with self.assertRaises(MidiError):
                    parameter_change(address, data, device)

    def test_decode_malformed_inputs_safely(self):
        for raw in (None, 5, "F0", [], b"", bytes.fromhex("F0 43 10 4C 00 00 7E 00")):
            with self.subTest(raw=raw):
                self.assertIsNone(decode_parameter_change(raw))

    def test_smf_conversion_rejects_non_byte_payload(self):
        for payload in (None, "43 10 F7", [0x43, 0x10, 0xf7], 3):
            with self.subTest(payload=payload):
                self.assertIsNone(smf_sysex_to_wire(0xf0, payload))

    def test_smf_sysex_opt_in(self):
        song = Song(0, 480, [Track([
            Event(0, 0xf0, bytes.fromhex("43 10 4C 00 00 7E 00 F7"), order=0),
            Event(0, 0x90, bytes((60, 100)), order=1)
        ])])
        self.assertEqual(len(list(timed_messages(song))), 1)
        self.assertEqual(list(timed_messages(song, include_sysex=True))[0][1], system_on())

    def test_incomplete_sysex_skipped(self):
        self.assertIsNone(smf_sysex_to_wire(0xf0, b"\x43\x10"))
        self.assertIsNone(smf_sysex_to_wire(0xf7, b"\x43\x10\xf7"))

if __name__ == "__main__":
    unittest.main()
