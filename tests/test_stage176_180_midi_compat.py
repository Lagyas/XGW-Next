import unittest
from midi import Song, Track, Event, MidiError
from midi_compat import sysex_profiles, track_ports, audit_roundtrip, GM_ON, GM2_ON, XG_ON


class MidiCompatTests(unittest.TestCase):
    def test_profiles(self):
        song = Song(1, 480, [Track([Event(0, 0xf0, data) for data in (GM_ON, GM2_ON, XG_ON)])])
        self.assertEqual(sysex_profiles(song), {'GM', 'GM2', 'XG'})

    def test_gs_checksum(self):
        payload = bytes.fromhex('41 10 42 12 40 00 7f 00 41 f7')
        self.assertEqual(sysex_profiles(Song(0, 480, [Track([Event(0, 0xf0, payload)])])), {'GS'})
        self.assertFalse(sysex_profiles(Song(0, 480, [Track([Event(0, 0xf0, payload[:-2] + b'\x00\xf7')])])) )

    def test_ports(self):
        song = Song(1, 480, [Track([Event(0, 0xff, b'\x02', 0x21)]), Track([])])
        self.assertEqual(track_ports(song), (2, None))

    def test_conflicting_ports(self):
        song = Song(1, 480, [Track([Event(0, 0xff, b'\x00', 0x21), Event(10, 0xff, b'\x01', 0x21)])])
        with self.assertRaises(MidiError): track_ports(song)

    def test_malformed_ports(self):
        song = Song(1, 480, [Track([Event(0, 0xff, b'\x00\x01', 0x21)])])
        with self.assertRaises(MidiError): track_ports(song)

    def test_roundtrip_preserves_sysex_port_and_chunks(self):
        song = Song(1, 480, [Track([Event(0, 0xff, b'\x01', 0x21),
                                   Event(0, 0xf0, XG_ON), Event(120, 0x90, b'\x3c\x64'),
                                   Event(240, 0x80, b'\x3c\x00')])],
                    extra_chunks=[(0, b'Xtra', b'keep')])
        song.dirty = True
        self.assertTrue(audit_roundtrip(song))

    def test_roundtrip_preserves_same_tick_events(self):
        song = Song(0, 480, [Track([Event(0, 0xb0, b'\x00\x7f'),
                                   Event(0, 0xc0, b'\x0a'), Event(0, 0x90, b'\x3c\x60')])])
        song.dirty = True
        self.assertTrue(audit_roundtrip(song))


if __name__ == '__main__': unittest.main()

class XGPortSafetyTests(unittest.TestCase):
    def test_xg_export_rejects_port_switch_on_same_track(self):
        from xg_export import export_xg
        song = Song(1, 480, [Track([Event(0, 0xff, b'\x00', 0x21),
                                   Event(120, 0xff, b'\x01', 0x21),
                                   Event(480, 0x90, b'\x3c\x40')])])
        with self.assertRaises(MidiError): export_xg(song, 2)

    def test_xg_export_rejects_malformed_port_metadata(self):
        from xg_export import export_xg
        song = Song(1, 480, [Track([Event(0, 0xff, b'\x00\x01', 0x21)])])
        with self.assertRaises(MidiError): export_xg(song, 2)
