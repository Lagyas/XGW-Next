import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from midi_demix import demix_to_format1

class DemixTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(0, 480, [Track([
            Event(0, 0xff, b'Piano', 3, 0),
            Event(0, 0xff, b'\x07\xa1\x20', 0x51, 1),
            Event(0, 0xf0, b'\x43\x10\x4c\xf7', order=2),
            Event(0, 0x90, b'\x3c\x64', order=3),
            Event(0, 0x91, b'\x40\x50', order=4),
            Event(240, 0x80, b'\x3c\x00', order=5),
            Event(480, 0x81, b'\x40\x00', order=6),
            Event(480, 0xff, b'', 0x2f, 7),
        ])])
    def test_format_and_channels(self):
        output = demix_to_format1(self.song)
        self.assertEqual((output.fmt, output.division, len(output.tracks)), (1, 480, 3))
        self.assertEqual([{e.channel() for e in t.events if e.channel()}
                          for t in output.tracks], [set(), {1}, {2}])
    def test_roundtrip_preserves_all_non_eot_events(self):
        result = Song.from_bytes(demix_to_format1(self.song).to_bytes())
        def signature(song):
            return sorted((e.tick, e.status, e.meta_type, e.data)
                          for track in song.tracks for e in track.events
                          if not (e.status == 0xff and e.meta_type in (0x2f, 0x03)))
        self.assertEqual(signature(result), signature(self.song))
    def test_original_untouched(self):
        raw = self.song.to_bytes()
        demix_to_format1(self.song)
        self.assertEqual(self.song.to_bytes(), raw)
        self.assertEqual(self.song.fmt, 0)
    def test_single_channel_track_not_split(self):
        s = Song(0, 480, [Track([Event(0, 0x92, b'\x3c\x40')])])
        result = demix_to_format1(s)
        self.assertEqual(len(result.tracks), 1)
        self.assertEqual(result.tracks[0].events[0].status, 0x92)
    def test_preserves_extension_chunks_at_split_boundaries(self):
        self.song.extra_chunks = [(0, b'PRE!', b'one'),
                                  (1, b'POST', b'two')]
        output = demix_to_format1(self.song)
        self.assertEqual(output.extra_chunks,
                         [(0, b'PRE!', b'one'), (3, b'POST', b'two')])
        raw = output.to_bytes()
        reloaded = Song.from_bytes(raw)
        self.assertEqual(reloaded.extra_chunks, output.extra_chunks)

    def test_preserves_header_extension(self):
        self.song.header_extra = b'\x12\x34'
        output = demix_to_format1(self.song)
        self.assertEqual(Song.from_bytes(output.to_bytes()).header_extra, b'\x12\x34')

    def test_preserves_extension_between_source_tracks(self):
        self.song.tracks.append(Track([Event(0, 0x92, b'\x45\x40')]))
        self.song.extra_chunks = [(1, b'META', b'boundary')]
        output = demix_to_format1(self.song)
        self.assertEqual(output.extra_chunks, [(3, b'META', b'boundary')])
        self.assertEqual(Song.from_bytes(output.to_bytes()).extra_chunks,
                         output.extra_chunks)

    def test_type2_rejected(self):
        with self.assertRaises(MidiError):
            demix_to_format1(Song(2, 480, [Track([])]))
    def test_existing_type1_mixed_track_split(self):
        s = Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x40'),
                                Event(0, 0x92, b'\x40\x40')])])
        self.assertEqual(len(demix_to_format1(s).tracks), 2)

if __name__ == '__main__':
    unittest.main()
