import unittest
from midi import MidiError, Song, Track, Event
from xg_effects import XGEffects, effects_from_song


class XGEffectsTests(unittest.TestCase):
    def test_reverb_address(self):
        model = XGEffects()
        model.set_type('reverb', 2, 3)
        self.assertEqual(model.message('reverb'), bytes.fromhex('F0 43 10 4C 02 01 00 02 03 F7'))

    def test_chorus_and_variation_addresses(self):
        model = XGEffects()
        model.set_type('chorus', 65, 1)
        model.set_type('variation', 5, 2)
        self.assertEqual(model.message('chorus', 3), bytes.fromhex('F0 43 13 4C 02 01 20 41 01 F7'))
        self.assertEqual(model.message('variation'), bytes.fromhex('F0 43 10 4C 02 01 40 05 02 F7'))

    def test_roundtrip(self):
        first, second = XGEffects(), XGEffects()
        first.set_type('variation', 17, 42)
        self.assertTrue(second.apply_sysex(first.message('variation')))
        self.assertEqual(second.types['variation'], (17, 42))

    def test_ignores_other_messages(self):
        model = XGEffects()
        self.assertFalse(model.apply_sysex(bytes.fromhex('F0 43 10 4C 00 00 7E 00 F7')))
        self.assertFalse(model.apply_sysex(bytes.fromhex('F0 43 10 4C 02 01 00 02 F7')))

    def test_invalid_input(self):
        model = XGEffects()
        for value in (-1, 128, True, 3.5):
            with self.assertRaises(MidiError):
                model.set_type('reverb', value, 0)
        with self.assertRaises(MidiError):
            model.set_type('unknown', 1, 0)
        with self.assertRaises(MidiError):
            model.message('unknown')

    def test_song_import_position(self):
        model = XGEffects()
        model.set_type('reverb', 2, 0)
        first = model.message('reverb')
        model.set_type('reverb', 3, 0)
        second = model.message('reverb')
        song = Song(1, 480, [Track([Event(0, 0xf0, first[1:]), Event(240, 0xf0, second[1:])])])
        self.assertEqual(effects_from_song(song, 0)[0].types['reverb'], (2, 0))
        self.assertEqual(effects_from_song(song, 240)[0].types['reverb'], (3, 0))
        self.assertEqual(effects_from_song(song)[1], 2)

    def test_invalid_position(self):
        for value in (-1, True, 1.2):
            with self.assertRaises(MidiError):
                effects_from_song(Song(0, 480, [Track()]), value)


class XGDeviceFilterTests(unittest.TestCase):
    def test_only_selected_device_is_imported(self):
        model = XGEffects()
        model.set_type('reverb', 2, 0)
        a = model.message('reverb', 0)
        model.set_type('reverb', 3, 0)
        b = model.message('reverb', 1)
        song = Song(1, 480, [Track([Event(0, 0xf0, a[1:]),
                                     Event(120, 0xf0, b[1:])])])
        self.assertEqual(effects_from_song(song, device=0)[0].types['reverb'], (2, 0))
        self.assertEqual(effects_from_song(song, device=0)[1], 1)
        self.assertEqual(effects_from_song(song, device=1)[0].types['reverb'], (3, 0))
        self.assertEqual(effects_from_song(song, device=1)[1], 1)
        self.assertEqual(effects_from_song(song)[1], 2)

    def test_reject_invalid_device_filter(self):
        for device in (-1, 16, True, '0'):
            with self.assertRaises(MidiError):
                effects_from_song(Song(0, 480, [Track()]), device=device)
            with self.assertRaises(MidiError):
                XGEffects().apply_sysex(b'', device=device)

    def test_filter_does_not_mutate_other_device(self):
        first = XGEffects()
        first.set_type('chorus', 66, 1)
        other = XGEffects()
        self.assertFalse(other.apply_sysex(first.message('chorus', 4), device=0))
        self.assertEqual(other.types['chorus'], (65, 0))


class WriteEffectsToSongTests(unittest.TestCase):
    def test_insert_roundtrip(self):
        from midi import Song, Track, Event
        from xg_effects import write_effect_types_to_song, effects_from_song
        song = Song(0, 480, [Track([Event(960, 0xff, b'', 0x2f)])])
        model = XGEffects()
        model.set_type('reverb', 2, 1)
        self.assertEqual(write_effect_types_to_song(song, model, 240, device=3), 3)
        self.assertTrue(song.dirty)
        restored = Song.from_bytes(song.to_bytes())
        read, count = effects_from_song(restored, through_tick=240, device=3)
        self.assertEqual(count, 3)
        self.assertEqual(read.types, model.types)
        self.assertEqual(effects_from_song(restored, 240, device=4)[1], 0)

    def test_invalid_is_atomic(self):
        from midi import Song, Track, Event, MidiError
        from xg_effects import write_effect_types_to_song
        song = Song(0, 480, [Track([Event(0, 0xff, b'', 0x2f)])])
        for tick, track, device in [(-1, 0, 0), (0, 1, 0), (0, 0, 16), (True, 0, 0)]:
            with self.assertRaises(MidiError):
                write_effect_types_to_song(song, XGEffects(), tick, track, device)
        self.assertEqual(len(song.tracks[0].events), 1)
        self.assertFalse(song.dirty)


class ReplaceEffectTypesTests(unittest.TestCase):
    def test_replace_same_device_tick_and_track_only(self):
        from xg_effects import write_effect_types_to_song
        old = XGEffects()
        old.set_type('reverb', 2, 0)
        unrelated = bytes.fromhex('F0 43 10 4C 00 00 7E 00 F7')
        song = Song(1, 480, [Track([
            Event(0, 0xf0, old.message('reverb', 2)[1:]),
            Event(0, 0xf0, old.message('chorus', 2)[1:]),
            Event(0, 0xf0, old.message('reverb', 3)[1:]),
            Event(240, 0xf0, old.message('reverb', 2)[1:]),
            Event(0, 0xf0, unrelated[1:]),
        ]), Track([Event(0, 0xf0, old.message('reverb', 2)[1:])])])
        new = XGEffects()
        new.set_type('reverb', 4, 0)
        self.assertEqual(write_effect_types_to_song(song, new, 0, device=2, replace=True), 3)
        self.assertEqual(len(song.tracks[0].events), 6)
        self.assertEqual(len(song.tracks[1].events), 1)
        self.assertEqual(effects_from_song(Song(0, 480, [song.tracks[0]]), 0, device=2)[0].types['reverb'], (4, 0))
        self.assertEqual(effects_from_song(song, 0, device=3)[0].types['reverb'], (2, 0))
        self.assertEqual(effects_from_song(Song(0, 480, [song.tracks[0]]), 240, device=2)[0].types['reverb'], (2, 0))

    def test_repeated_replace_does_not_accumulate(self):
        from xg_effects import write_effect_types_to_song
        song = Song(0, 480, [Track()])
        for _ in range(3):
            write_effect_types_to_song(song, XGEffects(), 0, replace=True)
        self.assertEqual(len(song.tracks[0].events), 3)
        restored = Song.from_bytes(song.to_bytes())
        self.assertEqual(effects_from_song(restored, 0, device=0)[1], 3)

    def test_invalid_replace_is_atomic(self):
        from xg_effects import write_effect_types_to_song
        song = Song(0, 480, [Track()])
        with self.assertRaises(MidiError):
            write_effect_types_to_song(song, XGEffects(), 0, replace=1)
        self.assertFalse(song.dirty)
        self.assertEqual(song.tracks[0].events, [])

class EffectInspectionValidationTests(unittest.TestCase):
    def test_malformed_effect_type_row_rejected(self):
        from xg_effects import format_effect_parameter_row
        with self.assertRaises(MidiError):
            format_effect_parameter_row((0, 0, 'reverb', (2, 1, 0), b'\x01'))

    def test_invalid_address_shape_rejected(self):
        from xg_effects import format_effect_parameter_row
        for address in (None, 42, b'\x02\x01\x00'):
            with self.assertRaises(MidiError):
                format_effect_parameter_row((0, 0, 'reverb', address, b'\x01\x00'))

    def test_empty_parameter_data_rejected(self):
        from xg_effects import format_effect_parameter_row
        with self.assertRaises(MidiError):
            format_effect_parameter_row((0, 0, 'chorus', (2, 1, 0x21), b''))

    def test_valid_parameter_still_formats(self):
        from xg_effects import format_effect_parameter_row
        row = format_effect_parameter_row((120, 0, 'variation', (2, 1, 0x41), b'\x40'))
        self.assertEqual(row[3], 'Parameter +01')
