import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import MidiError
from xg_parts import XGParts
from xg_sysex import decode_parameter_change

class XGPartTests(unittest.TestCase):
    def test_part_volume_address(self):
        model = XGParts()
        model.set(3, "volume", 87)
        message = model.message(3, "volume")
        self.assertEqual(message, bytes.fromhex("F0 43 10 4C 08 03 0B 57 F7"))
        self.assertEqual(decode_parameter_change(message)["data"], b"\x57")

    def test_roundtrip_model(self):
        a, b = XGParts(), XGParts()
        a.set(5, "pan", 12)
        self.assertTrue(b.apply_sysex(a.message(5, "pan")))
        self.assertEqual(b.parts[5].pan, 12)

    def test_reject_invalid_value(self):
        model = XGParts()
        with self.assertRaises(MidiError):
            model.set(0, "volume", 128)

    def test_non_part_message_ignored(self):
        model = XGParts()
        self.assertFalse(model.apply_sysex(bytes.fromhex("F0 43 10 4C 00 00 7E 00 F7")))

if __name__ == "__main__":
    unittest.main()

class XGImportTests(unittest.TestCase):
    def test_import_part_settings_from_smf(self):
        from midi import Song, Track, Event
        from xg_parts import parts_from_song
        model = XGParts()
        model.set(2, 'volume', 91)
        raw = model.message(2, 'volume')
        song = Song(1, 480, [Track([Event(120, 0xf0, raw[1:])])])
        loaded, count = parts_from_song(song)
        self.assertEqual(count, 1)
        self.assertEqual(loaded.parts[2].volume, 91)

    def test_import_position_and_track_order(self):
        from midi import Song, Track, Event
        from xg_parts import parts_from_song
        model = XGParts()
        model.set(0, 'pan', 15)
        first = model.message(0, 'pan')
        model.set(0, 'pan', 85)
        second = model.message(0, 'pan')
        song = Song(1, 480, [Track([Event(0, 0xf0, first[1:])]),
                              Track([Event(240, 0xf0, second[1:])])])
        self.assertEqual(parts_from_song(song, 0)[0].parts[0].pan, 15)
        self.assertEqual(parts_from_song(song, 240)[0].parts[0].pan, 85)

    def test_ignores_unrelated_and_incomplete_sysex(self):
        from midi import Song, Track, Event
        from xg_parts import parts_from_song
        song = Song(0, 480, [Track([Event(0, 0xf0, b'\x7e\x7f\x09\x01\xf7'),
                                    Event(1, 0xf7, b'\x43\x10\x4c\x08\x00\x0b\x50\xf7'),
                                    Event(2, 0xf0, b'\x43\x10')])])
        self.assertEqual(parts_from_song(song)[1], 0)

    def test_invalid_position(self):
        from midi import Song, Track, MidiError
        from xg_parts import parts_from_song
        for value in (-1, True, 1.2):
            with self.assertRaises(MidiError):
                parts_from_song(Song(0, 480, [Track()]), value)

class XGVariationTests(unittest.TestCase):
    def test_variation_send_wire_address(self):
        model = XGParts()
        model.set(4, "variation_send", 64)
        self.assertEqual(model.message(4, "variation_send"),
                         bytes.fromhex("F0 43 10 4C 08 04 14 40 F7"))

    def test_variation_send_roundtrip(self):
        source, target = XGParts(), XGParts()
        source.set(15, "variation_send", 127)
        self.assertTrue(target.apply_sysex(source.message(15, "variation_send")))
        self.assertEqual(target.parts[15].variation_send, 127)

    def test_variation_send_out_of_range(self):
        model = XGParts()
        for value in (-1, 128):
            with self.assertRaises(MidiError):
                model.set(0, "variation_send", value)

    def test_variation_send_song_import(self):
        from midi import Song, Track, Event
        from xg_parts import parts_from_song
        model = XGParts()
        model.set(1, "variation_send", 90)
        wire = model.message(1, "variation_send")
        song = Song(0, 480, [Track([Event(0, 0xf0, wire[1:])])])
        loaded, count = parts_from_song(song)
        self.assertEqual(count, 1)
        self.assertEqual(loaded.parts[1].variation_send, 90)

class XGDeviceTests(unittest.TestCase):
    def test_device_number_in_sysex(self):
        model = XGParts()
        self.assertEqual(model.message(0, "volume", device=5),
                         bytes.fromhex("F0 43 15 4C 08 00 0B 64 F7"))

    def test_device_number_bounds(self):
        model = XGParts()
        for device in (-1, 16, 128):
            with self.assertRaises(MidiError):
                model.message(0, "volume", device=device)
