import sys
import unittest
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Event, Track
from midi_demix import demix_to_format1

class DemixReferenceTests(unittest.TestCase):
    def test_split_tracks_named_and_separated(self):
        song = Song(0, 480, [Track([Event(0,255,b'Keys',3), Event(0,0x90,b'\x3c\x40'), Event(0,0x91,b'\x40\x40')])])
        result = Song.from_bytes(demix_to_format1(song).to_bytes())
        self.assertEqual([t.name() for t in result.tracks], ['Keys', 'Keys [ch 1]', 'Keys [ch 2]'])
        for track in result.tracks:
            self.assertLessEqual(len({e.status & 15 for e in track.events if 0x80 <= e.status <= 0xef}), 1)

    def test_events_preserved_except_new_track_names_and_eot(self):
        song = Song(0, 480, [Track([Event(0,255,b'Keys',3), Event(0,0x90,b'\x3c\x40'), Event(0,0x91,b'\x40\x40'), Event(200,0x81,b'\x40\x00')])])
        result = Song.from_bytes(demix_to_format1(song).to_bytes())
        def sig(s):
            return Counter((e.tick,e.status,e.meta_type,e.data) for t in s.tracks for e in t.events if not (e.status==255 and e.meta_type in (3,47)))
        self.assertEqual(sig(song),sig(result))
