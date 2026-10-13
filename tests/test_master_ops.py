import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, Track, Event, MidiError
from master_ops import (master_events, tempo_payload, time_signature_payload,
                        put_master_event, delete_master_event)

class MasterOpsTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(1, 480, [Track([Event(0, 0xff, b"", 0x2f, 0)]),
                                  Track([Event(0, 0xff, b"", 0x2f, 0)])])

    def test_tempo_roundtrip(self):
        index = put_master_event(self.song, 960, 0x51, tempo_payload(120))
        self.assertEqual(index, 1)
        parsed = Song.from_bytes(self.song.to_bytes())
        events = master_events(parsed)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][2].tick, 960)
        self.assertEqual(events[0][2].data, bytes.fromhex("07 a1 20"))

    def test_signature_update_delete(self):
        index = put_master_event(self.song, 0, 0x58, time_signature_payload(3, 4))
        put_master_event(self.song, 480, 0x58, time_signature_payload(7, 8),
                         event_index=index)
        self.assertEqual(master_events(self.song)[0][2].data[:2], bytes((7, 3)))
        delete_master_event(self.song, 0, index)
        self.assertEqual(master_events(self.song), [])

    def test_invalid_input_is_atomic(self):
        before = len(self.song.tracks[0].events)
        with self.assertRaises(MidiError):
            put_master_event(self.song, -1, 0x51, tempo_payload(120))
        with self.assertRaises(MidiError):
            time_signature_payload(4, 3)
        with self.assertRaises(MidiError):
            tempo_payload(0)
        self.assertEqual(len(self.song.tracks[0].events), before)

    def test_protect_other_meta_events(self):
        with self.assertRaises(MidiError):
            delete_master_event(self.song, 0, 0)

if __name__ == "__main__":
    unittest.main()
