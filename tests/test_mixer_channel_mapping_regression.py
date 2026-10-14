import unittest
from midi import Song, Track, Event, MidiError
from xg_mixer_bridge import mixer_channel_snapshot
from xg_sysex import parameter_change


class MixerMappingRegression(unittest.TestCase):
    def song(self):
        song = Song(1, 480, [Track([])])
        song.tracks[0].events.extend([
            Event(0, 0xb4, bytes([7, 41]), order=0),  # MIDI channel 5
            Event(0, 0xb1, bytes([7, 98]), order=1),  # MIDI channel 2
            Event(0, 0xf0, parameter_change((8, 8, 0x0b), (72,), 3)[1:], order=2),
        ])
        return song

    def test_channel_is_not_confused_with_device(self):
        values, sources = mixer_channel_snapshot(self.song(), 5, (9, 3), 0)
        self.assertEqual(values['Volume'], 72)
        self.assertEqual(sources['Volume'], 'XG SysEx')

    def test_other_device_does_not_override_channel_cc(self):
        values, sources = mixer_channel_snapshot(self.song(), 5, (9, 2), 0)
        self.assertEqual(values['Volume'], 41)
        self.assertEqual(sources['Volume'], 'CC')

    def test_different_channel_uses_its_own_cc(self):
        values, _ = mixer_channel_snapshot(self.song(), 2, (9, 2), 0)
        self.assertEqual(values['Volume'], 98)

    def test_invalid_mapping_rejected(self):
        for channel, assignment in [(True, (9, 3)), (0, (9, 3)), (5, (9,)), (5, '9,3'), (5, (17, 3)), (5, (9, 16))]:
            with self.subTest(channel=channel, assignment=assignment), self.assertRaises(MidiError):
                mixer_channel_snapshot(self.song(), channel, assignment)
