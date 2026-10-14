import sys
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from xws_probe import inspect_xws, format_report

HEADER = b'MThd' + b'\x00\x00\x00\x06\x00\x01\x00\x01\x01\xe0'
TRACK = b'MTrk' + b'\x00\x00\x00\x04\x00\xff\x2f\x00'

class XwsProbeTests(unittest.TestCase):
    def inspect(self, data):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'sample.xws'
            path.write_bytes(data)
            self.assertEqual(path.read_bytes(), data)
            result = inspect_xws(path)
            self.assertEqual(path.read_bytes(), data)
            return result

    def test_empty(self):
        result = self.inspect(b'')
        self.assertEqual(result.embedded_midi, ())
        self.assertEqual(result.size, 0)

    def test_unknown_binary(self):
        self.assertEqual(self.inspect(b'XWS\x00' + bytes(100)).embedded_midi, ())

    def test_embedded_midi_candidate(self):
        report = self.inspect(b'legacy-data' + HEADER + TRACK)
        self.assertEqual(len(report.embedded_midi), 1)
        self.assertEqual(report.embedded_midi[0].offset, 11)
        self.assertIn('Offset 11', format_report(report))

    def test_reject_false_header(self):
        self.assertEqual(self.inspect(HEADER + b'junk' + TRACK).embedded_midi, ())

    def test_reject_truncated_track(self):
        self.assertEqual(self.inspect(HEADER + b'MTrk' + b'\xff\xff\xff\xff').embedded_midi, ())

    def test_does_not_claim_import(self):
        self.assertIn('not available yet', format_report(self.inspect(HEADER + TRACK)))
