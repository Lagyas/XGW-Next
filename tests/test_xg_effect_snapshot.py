import unittest
from midi import Song, Track, Event, MidiError
from xg_effects import write_effect_parameter_to_song, effect_parameters_at_tick


class EffectSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(0, 480, [Track([Event(960, 0xff, b'', 0x2f)])])

    def test_latest_value_before_position(self):
        write_effect_parameter_to_song(self.song, 'reverb', 3, [10], 100)
        write_effect_parameter_to_song(self.song, 'reverb', 3, [20], 200)
        self.assertEqual(effect_parameters_at_tick(self.song, 150)[('reverb', 3)], b'\x0a')
        self.assertEqual(effect_parameters_at_tick(self.song, 200)[('reverb', 3)], b'\x14')

    def test_device_isolation(self):
        write_effect_parameter_to_song(self.song, 'chorus', 2, [11], 10, device=0)
        write_effect_parameter_to_song(self.song, 'chorus', 2, [22], 10, device=1)
        self.assertEqual(effect_parameters_at_tick(self.song, 10, device=1), {('chorus', 2): b'\x16'})

    def test_empty_before_first_event(self):
        write_effect_parameter_to_song(self.song, 'variation', 4, [5], 30)
        self.assertEqual(effect_parameters_at_tick(self.song, 29), {})

    def test_invalid_arguments(self):
        for tick, device in [(-1, 0), (True, 0), (0, 16), (0, False)]:
            with self.subTest(tick=tick, device=device), self.assertRaises(MidiError):
                effect_parameters_at_tick(self.song, tick, device)

    def test_effect_filter(self):
        write_effect_parameter_to_song(self.song, 'reverb', 2, [10], 0)
        write_effect_parameter_to_song(self.song, 'chorus', 2, [20], 0)
        self.assertEqual(effect_parameters_at_tick(self.song, 0, effect='chorus'), {('chorus', 2): b'\x14'})
