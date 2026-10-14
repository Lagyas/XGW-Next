import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from midi import Song, Track, MidiError
from project_bundle import save_project, load_project, load_project_track_properties
from xws_track_properties import validate_track_properties

class TrackPropertiesTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [Track(), Track()])
        self.props = {'source': 'XGworks S4WT', 'tracks': [
            {'track': 1, 'channel': 5, 'verified': True},
            {'track': 2, 'channel': None, 'verified': False}]}

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'song.xgwn'
            save_project(path, self.song, xws_track_properties=self.props)
            self.assertEqual(load_project_track_properties(path, 2), self.props)
            self.assertEqual(len(load_project(path)[0].tracks), 2)

    def test_legacy_project_has_no_properties(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'song.xgwn'
            save_project(path, self.song)
            self.assertIsNone(load_project_track_properties(path, 2))

    def test_invalid_channel_rejected(self):
        self.props['tracks'][0]['channel'] = 17
        with self.assertRaises(MidiError):
            validate_track_properties(self.props, 2)

    def test_duplicate_track_rejected(self):
        self.props['tracks'][1]['track'] = 1
        with self.assertRaises(MidiError):
            validate_track_properties(self.props, 2)

    def test_unverified_value_rejected(self):
        self.props['tracks'][0]['verified'] = False
        with self.assertRaises(MidiError):
            validate_track_properties(self.props, 2)

if __name__ == '__main__':
    unittest.main()
