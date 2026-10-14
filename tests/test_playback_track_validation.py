import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, MidiError
from midi_output import validate_enabled_tracks, timed_messages, chase_messages, MidiPlayer


class PlaybackTrackValidationTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [Track([]), Track([])])

    def test_accepts_valid_selection_and_none(self):
        self.assertIsNone(validate_enabled_tracks(self.song, None))
        self.assertEqual(validate_enabled_tracks(self.song, [1, 0, 1]), {0, 1})
        self.assertEqual(validate_enabled_tracks(self.song, []), set())

    def test_rejects_invalid_track_ids(self):
        for selected in ([2], [-1], [True], ['1'], [0.5], 42):
            with self.subTest(selected=selected), self.assertRaises(MidiError):
                validate_enabled_tracks(self.song, selected)

    def test_rejects_invalid_selection_before_timeline(self):
        with self.assertRaises(MidiError):
            list(timed_messages(self.song, enabled_tracks={2}))
        with self.assertRaises(MidiError):
            chase_messages(self.song, 0, enabled_tracks={2})

    def test_play_rejects_invalid_tracks_before_thread_start(self):
        player = MidiPlayer()
        with self.assertRaises(MidiError):
            player.play(self.song, 'dummy-port', enabled_tracks={2})
        self.assertFalse(player.playing)
