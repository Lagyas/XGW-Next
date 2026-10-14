import unittest
from midi import Song, Track, Event
from midi_output import timed_messages, chase_messages, loop_messages


class MixerChannelFilterTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [Track([
            Event(0, 0x90, bytes((60, 90))),
            Event(0, 0x91, bytes((62, 90))),
            Event(240, 0x80, bytes((60, 0))),
            Event(240, 0x81, bytes((62, 0))),
        ])])

    def test_channel_mute_filter(self):
        result = list(timed_messages(self.song, enabled_channels={0}))
        self.assertEqual([payload[0] for _, payload in result], [0x90, 0x80])

    def test_empty_channels_silences_all(self):
        self.assertEqual(list(timed_messages(self.song, enabled_channels=set())), [])

    def test_chase_obeys_channel_filter(self):
        self.song.tracks[0].events.insert(0, Event(0, 0xb1, bytes((7, 50))))
        self.song.tracks[0].events.insert(0, Event(0, 0xb0, bytes((7, 80))))
        self.assertEqual(chase_messages(self.song, 100, enabled_channels={0}),
                         [bytes((0xb0, 7, 80))])

    def test_loop_obeys_channel_filter(self):
        timeline, duration = loop_messages(self.song, 0, 480, enabled_channels={1})
        self.assertGreater(duration, 0)
        self.assertEqual([payload[0] for _, payload in timeline], [0x91, 0x81])
