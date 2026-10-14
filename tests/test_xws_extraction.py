import sys
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import MidiError, Song
from xws_probe import inspect_xws, extract_embedded_smf

HEADER = b'MThd\x00\x00\x00\x06\x00\x01\x00\x01\x01\xe0'
TRACK = b'MTrk\x00\x00\x00\x04\x00\xff\x2f\x00'

class XwsExtractionTests(unittest.TestCase):
    def check(self, data, offset):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'legacy.xws'
            source.write_bytes(data)
            original = source.read_bytes()
            try:
                result = extract_embedded_smf(source, offset)
            finally:
                self.assertEqual(source.read_bytes(), original)
            return result

    def test_extract_complete_midi_and_ignore_trailing_xws(self):
        data = b'XWS unknown' + HEADER + TRACK + b'other legacy chunks'
        self.assertEqual(self.check(data, 11), HEADER + TRACK)
        self.assertEqual(len(Song.from_bytes(self.check(data, 11)).tracks), 1)

    def test_reject_incomplete_track_count(self):
        header = HEADER[:10] + b'\x00\x02' + HEADER[12:]
        with self.assertRaises(MidiError): self.check(header + TRACK, 0)

    def test_reject_invalid_event_stream(self):
        invalid = b'MTrk\x00\x00\x00\x02\x00\x90'
        with self.assertRaises(MidiError): self.check(HEADER + invalid, 0)

    def test_reject_bad_offset(self):
        with self.assertRaises(ValueError): self.check(HEADER + TRACK, -1)

    def test_probe_candidate_can_be_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'song.xws'
            path.write_bytes(b'prefix' + HEADER + TRACK)
            candidate = inspect_xws(path).embedded_midi[0]
            self.assertEqual(extract_embedded_smf(path, candidate.offset), HEADER + TRACK)
