import unittest
from xws_experiment import compare_xws_binary_evidence


def sample():
    return chunk(b'S4WH', bytes(64)) + chunk(b'S4WB', b'\x00\xb0\x0a\x40') + chunk(b'S4WT', bytes(33)) + chunk(b'S4ST', b'')


def chunk(tag, payload):
    return tag + len(payload).to_bytes(4, 'big') + payload


class PanEvidenceTests(unittest.TestCase):
    def test_reject_non_bytes(self):
        with self.assertRaises(TypeError):
            compare_xws_binary_evidence('x', b'')

    def test_identical_empty_chunk_sequence(self):
        self.assertEqual(compare_xws_binary_evidence(sample(), sample())['changed_chunks'], [])

    def test_added_trailing_chunks(self):
        before = sample() + chunk(b'SCRS', b'\0\0\0\0')
        after = before + chunk(b'SCRA', b'\0\0\0\0')
        result = compare_xws_binary_evidence(before, after)
        self.assertEqual(result['changed_chunks'][-1]['kind'], 'SCRA')
        self.assertTrue(result['changed_chunks'][-1]['added'])

    def test_changed_chunk_sequences_rejected(self):
        from midi import MidiError
        with self.assertRaises(MidiError):
            compare_xws_binary_evidence(sample() + chunk(b'SCRS', b'\0'*4), sample() + chunk(b'SCRA', b'\0'*4))
