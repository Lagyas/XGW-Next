import unittest
from xws_channel_evidence import compare_track_channel_edit
from midi import MidiError


def chunk(tag, payload):
    return tag + len(payload).to_bytes(4, 'big') + payload


def sample(channel=0):
    meta = bytearray(33)
    meta[2] = channel
    return chunk(b'S4WH', bytes(64)) + chunk(b'S4WB', b'') + chunk(b'S4WT', meta)


class ChannelEvidenceTests(unittest.TestCase):
    def test_one_s4wt_candidate(self):
        result = compare_track_channel_edit(sample(0), sample(1))
        self.assertEqual(result['s4wt_candidates'][0]['fixed_prefix_changes'], [(2, 0, 1)])
        self.assertFalse(result['verified_channel_decoder'])

    def test_added_chunks(self):
        result = compare_track_channel_edit(sample(), sample() + chunk(b'SCRS', bytes(4)))
        self.assertEqual(result['added_chunks'], ['SCRS'])

    def test_reject_reordered_chunks(self):
        with self.assertRaises(MidiError):
            compare_track_channel_edit(sample(), chunk(b'S4WH', bytes(64)) + chunk(b'S4WT', bytes(33)))

    def test_reject_nonbytes(self):
        with self.assertRaises(TypeError):
            compare_track_channel_edit('x', sample())
