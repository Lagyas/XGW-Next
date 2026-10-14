import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, Track, Event, MidiError

class MidiIntegrityTests(unittest.TestCase):
    def song(self, event):
        result = Song(1, 480, [Track([event])])
        result.dirty = True
        return result

    def test_invalid_channel_payload_rejected(self):
        for status, payload in ((0x90, b"\x3c"), (0xc0, b"\x01\x02"), (0xb0, b"\x01\x80")):
            with self.subTest(status=status, payload=payload):
                with self.assertRaises(MidiError):
                    self.song(Event(0, status, payload)).to_bytes()

    def test_invalid_meta_and_status_rejected(self):
        for event in (Event(0, 0xff, b"", 256), Event(0, 0xf1, b""), Event(0, 0x70, b"")):
            with self.subTest(status=event.status):
                with self.assertRaises(MidiError):
                    self.song(event).to_bytes()

    def test_valid_sysex_tempo_and_channel_roundtrip(self):
        events = [Event(0, 0xff, b"\x07\xa1\x20", 0x51),
                  Event(0, 0xf0, b"\x43\x10\x4c\x00\xf7"),
                  Event(10, 0x91, b"\x40\x60")]
        song = Song(1, 480, [Track(events)])
        song.dirty = True
        parsed = Song.from_bytes(song.to_bytes())
        self.assertEqual([(e.tick,e.status,e.meta_type,e.data) for e in parsed.tracks[0].events],
                         [(e.tick,e.status,e.meta_type,e.data) for e in events])
