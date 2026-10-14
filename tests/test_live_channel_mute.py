import unittest
from midi_output import MidiPlayer
from midi import MidiError


class LiveChannelMuteTests(unittest.TestCase):
    def test_change_and_pending_silence(self):
        player = MidiPlayer()
        player.set_enabled_channels({0, 1, 9})
        enabled, silenced = player._current_channel_state()
        self.assertEqual(enabled, {0, 1, 9})
        self.assertEqual(silenced, set(range(16)) - enabled)
        self.assertEqual(player._current_channel_state()[1], set())

    def test_reenable_channel(self):
        player = MidiPlayer()
        player.set_enabled_channels({0})
        player._current_channel_state()
        player.set_enabled_channels({0, 2})
        self.assertEqual(player._current_channel_state(), ({0, 2}, set()))

    def test_reject_invalid_channels(self):
        player = MidiPlayer()
        for channels in ({16}, {-1}, {1.0}):
            with self.assertRaises(MidiError):
                player.set_enabled_channels(channels)
