import unittest
from midi import MidiError
from xws_track_display import source_channel_labels


class SourceChannelDisplayTests(unittest.TestCase):
    def test_no_source(self):
        self.assertEqual(source_channel_labels(None, 3), ('—', '—', '—'))

    def test_known_and_unknown(self):
        value = {'source': 'XGworks S4WT', 'tracks': [
            {'track': 2, 'channel': 5, 'verified': True},
            {'track': 1, 'channel': None, 'verified': False}]}
        self.assertEqual(source_channel_labels(value, 3), ('?', '5', '—'))

    def test_does_not_mutate(self):
        value = {'source': 'XGworks S4WT', 'tracks': [{'track': 1, 'channel': 16, 'verified': True}]}
        self.assertEqual(source_channel_labels(value, 1), ('16',))
        self.assertEqual(value['tracks'][0]['channel'], 16)

    def test_invalid_source_rejected(self):
        with self.assertRaises(MidiError):
            source_channel_labels({'source': 'other', 'tracks': []}, 1)

    def test_invalid_count(self):
        with self.assertRaises(ValueError):
            source_channel_labels(None, -1)
