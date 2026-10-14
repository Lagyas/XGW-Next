import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import MidiError
from midi_output import MidiPlayer, validate_enabled_channels


class PlaybackChannelValidationTests(unittest.TestCase):
    def test_accepts_valid_channel_set(self):
        self.assertEqual(validate_enabled_channels([0, 9, 15, 9]), {0, 9, 15})

    def test_rejects_invalid_channel_types_and_ranges(self):
        for channels in ([16], [-1], [True], ['9'], None, [1.5]):
            with self.subTest(channels=channels), self.assertRaises(MidiError):
                validate_enabled_channels(channels)

    def test_live_update_rejects_invalid_channels_without_mutation(self):
        player = MidiPlayer()
        player.set_enabled_channels({0, 1})
        with self.assertRaises(MidiError):
            player.set_enabled_channels({0, 16})
        self.assertEqual(player._enabled_channels, {0, 1})

    def test_play_rejects_invalid_mask_before_opening_midi_port(self):
        player = MidiPlayer()
        with self.assertRaises(MidiError):
            player.play(None, 'dummy-port', enabled_channels={False})
        self.assertFalse(player.playing)
