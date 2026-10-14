import unittest
from midi import Song, Track, Event, MidiError
from xg_sysex import parameter_change
from xg_effects import inspect_effect_parameter_changes


class XGEffectInspectionTests(unittest.TestCase):
    def test_identifies_all_three_effect_blocks(self):
        addresses = [(2, 1, 3), (2, 1, 0x25), (2, 1, 0x5f)]
        song = Song(0, 480, [Track([
            Event(i * 120, 0xf0, parameter_change(addr, (7,), 2)[1:])
            for i, addr in enumerate(addresses)
        ])])
        rows = inspect_effect_parameter_changes(song, device=2)
        self.assertEqual([r[2] for r in rows], ['reverb', 'chorus', 'variation'])
        self.assertEqual([r[3] for r in rows], addresses)
        self.assertEqual([r[4] for r in rows], [b'\x07'] * 3)
        self.assertEqual(len(inspect_effect_parameter_changes(song, through_tick=120)), 2)

    def test_ignores_other_devices_and_addresses(self):
        song = Song(0, 480, [Track([
            Event(0, 0xf0, parameter_change((2, 1, 1), (8,), 1)[1:]),
            Event(0, 0xf0, parameter_change((2, 2, 1), (8,), 0)[1:]),
            Event(0, 0xf0, parameter_change((2, 1, 0x60), (8,), 0)[1:]),
            Event(0, 0xf7, b'\x43\x10\x4c'),
        ])])
        self.assertEqual(inspect_effect_parameter_changes(song, device=0), [])
        self.assertEqual(len(inspect_effect_parameter_changes(song, device=1)), 1)

    def test_rejects_invalid_filters(self):
        song = Song(0, 480, [Track()])
        for value in (-1, True, 1.2):
            with self.assertRaises(MidiError):
                inspect_effect_parameter_changes(song, through_tick=value)
        for value in (-1, 16, True):
            with self.assertRaises(MidiError):
                inspect_effect_parameter_changes(song, device=value)

    def test_does_not_mutate_song(self):
        song = Song(0, 480, [Track([Event(0, 0xf0,
            parameter_change((2, 1, 0x42), (3, 4))[1:])])])
        before = song.to_bytes()
        inspect_effect_parameter_changes(song)
        self.assertEqual(song.to_bytes(), before)
        self.assertFalse(song.dirty)


class XGEffectRowFormattingTests(unittest.TestCase):
    def test_type_row(self):
        from xg_effects import format_effect_parameter_row
        self.assertEqual(format_effect_parameter_row((480, 0, 'reverb', (2, 1, 0), bytes([1, 0]))),
                         ('480', '1', 'Reverb', 'Effect Type', '02 01 00', '01 00'))

    def test_unknown_offset_preserved(self):
        from xg_effects import format_effect_parameter_row
        self.assertEqual(format_effect_parameter_row((0, 2, 'variation', (2, 1, 0x43), bytes([127])))[3:],
                         ('Parameter +03', '02 01 43', '7F'))

    def test_reject_wrong_block(self):
        from xg_effects import format_effect_parameter_row
        with self.assertRaises(MidiError):
            format_effect_parameter_row((0, 0, 'reverb', (2, 1, 0x40), bytes([1])))
