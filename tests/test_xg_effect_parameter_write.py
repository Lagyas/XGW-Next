import unittest
from midi import MidiError, Song, Track, Event
from xg_effects import write_effect_parameter_to_song, inspect_effect_parameter_changes


class RawEffectParameterWriteTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(0, 480, [Track([Event(960, 0xff, b'', 0x2f)])])

    def test_roundtrip(self):
        write_effect_parameter_to_song(self.song, 'chorus', 3, (20,), 120, device=4)
        restored = Song.from_bytes(self.song.to_bytes())
        rows = inspect_effect_parameter_changes(restored, device=4)
        self.assertEqual(rows[0][2:5], ('chorus', (2, 1, 0x23), b'\x14'))

    def test_replace_is_scoped_to_device_address_and_tick(self):
        for device, tick, offset, value in [(0, 120, 3, 10), (1, 120, 3, 20),
                                             (0, 121, 3, 30), (0, 120, 4, 40)]:
            write_effect_parameter_to_song(self.song, 'reverb', offset, (value,), tick, device=device)
        write_effect_parameter_to_song(self.song, 'reverb', 3, (99,), 120, replace=True)
        rows = inspect_effect_parameter_changes(self.song)
        self.assertEqual(len(rows), 4)
        self.assertEqual([row[4] for row in rows].count(b'\x63'), 1)
        self.assertEqual([row[4] for row in rows].count(b'\x0a'), 0)

    def test_invalid_input_is_atomic(self):
        for kwargs in [dict(effect='bad'), dict(offset=32), dict(values=(128,)),
                       dict(tick=-1), dict(device=16), dict(track_index=1),
                       dict(values=(True,)), dict(offset=0, values=(1,))]:
            options = dict(effect='variation', offset=1, values=(2,), tick=0)
            options.update(kwargs)
            with self.assertRaises(MidiError):
                write_effect_parameter_to_song(self.song, **options)
        self.assertEqual(len(self.song.tracks[0].events), 1)
        self.assertFalse(self.song.dirty)

    def test_append_keeps_previous(self):
        write_effect_parameter_to_song(self.song, 'variation', 1, (1,), 0)
        write_effect_parameter_to_song(self.song, 'variation', 1, (2,), 0)
        self.assertEqual(len(inspect_effect_parameter_changes(self.song)), 2)
