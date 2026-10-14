import unittest
from midi import Song, Track, Event, MidiError
from midi_compat import audit_roundtrip, track_ports, sysex_profiles, XG_ON
from xg_export import export_xg


class Stage236240IntegrityTests(unittest.TestCase):
    def test_atomic_set_event_rejects_invalid_data_after_valid_tick(self):
        e = Event(12, 0x90, b'\x3c\x40')
        song = Song(0, 480, [Track([e])])
        with self.assertRaises(MidiError):
            song.set_event(0, 0, tick=100, data=b'\x80\x40')
        self.assertEqual((e.tick, e.data, song.dirty), (12, b'\x3c\x40', False))

    def test_noop_does_not_dirty_original(self):
        song = Song(0, 480, [Track([Event(12, 0x90, b'\x3c\x40')])])
        self.assertFalse(song.set_event(0, 0, tick=12, data=b'\x3c\x40'))
        self.assertFalse(song.dirty)

    def test_rejects_bad_ticks_and_boolean_bytes(self):
        song = Song(0, 480, [Track([Event(12, 0x90, b'\x3c\x40')])])
        for value in (-1, True, 0x10000000, 1.5):
            with self.subTest(value=value), self.assertRaises(MidiError):
                song.set_event(0, 0, tick=value)
        with self.assertRaises(MidiError):
            song.set_event(0, 0, data=[True, 64])
        self.assertFalse(song.dirty)

    def test_roundtrip_detects_same_tick_reorder(self):
        song = Song(0, 480, [Track([Event(0, 0xb0, b'\x00\x7f', order=0),
                                   Event(0, 0xc0, b'\x0a', order=1)])])
        song.dirty = True
        self.assertTrue(audit_roundtrip(song))

    def test_sysex_and_ports_survive_edited_smf(self):
        song = Song(1, 480, [Track([Event(0, 0xff, b'\x00', 0x21),
                                   Event(0, 0xf0, XG_ON),
                                   Event(120, 0x90, b'\x3c\x40')])])
        song.set_event(0, 2, tick=140)
        restored = Song.from_bytes(song.to_bytes())
        self.assertEqual(track_ports(restored), (0,))
        self.assertIn('XG', sysex_profiles(restored))
        self.assertTrue(audit_roundtrip(song))

    def test_xg_export_rejects_unmapped_port(self):
        song = Song(1, 480, [Track([Event(0, 0xff, b'\x02', 0x21),
                                   Event(120, 0x90, b'\x3c\x40')])])
        with self.assertRaises(MidiError):
            export_xg(song, 2)


if __name__ == '__main__':
    unittest.main()
