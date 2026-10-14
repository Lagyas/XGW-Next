import unittest
from track_channel_properties import channel_override_label, parse_channel_override


class TrackChannelPropertiesTests(unittest.TestCase):
    def test_keep_roundtrip(self):
        self.assertIsNone(parse_channel_override(channel_override_label(None)))

    def test_all_channels_roundtrip(self):
        for channel in range(16):
            with self.subTest(channel=channel):
                self.assertEqual(parse_channel_override(channel_override_label(channel)), channel)

    def test_invalid_internal_channel(self):
        for channel in (-1, 16, True, '1'):
            with self.subTest(channel=channel):
                with self.assertRaises(ValueError):
                    channel_override_label(channel)

    def test_invalid_input(self):
        for label in ('0', '17', '01', '-1', ' 1', '1 ', '１', None, 1, ''):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    parse_channel_override(label)

    def test_no_source_mutation(self):
        events = [bytes([0x90, 60, 100]), bytes([0x80, 60, 0])]
        before = list(events)
        parse_channel_override('5')
        self.assertEqual(events, before)
