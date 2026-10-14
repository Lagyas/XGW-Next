import unittest
from types import SimpleNamespace
from mixer_track_sync import destination_for_selection


class MixerTrackSyncTests(unittest.TestCase):
    def setUp(self):
        self.song = SimpleNamespace(tracks=[object(), object(), object()])

    def test_first_track(self):
        self.assertEqual(destination_for_selection(self.song, 0, 3), 1)

    def test_last_track(self):
        self.assertEqual(destination_for_selection(self.song, 2, 1), 3)

    def test_missing_selection_preserves_destination(self):
        self.assertEqual(destination_for_selection(self.song, None, 2), 2)

    def test_out_of_range_preserves_destination(self):
        self.assertEqual(destination_for_selection(self.song, 3, 2), 2)

    def test_invalid_boolean_preserves_destination(self):
        self.assertEqual(destination_for_selection(self.song, True, 2), 2)

    def test_missing_song_preserves_destination(self):
        self.assertEqual(destination_for_selection(None, 0, 2), 2)
