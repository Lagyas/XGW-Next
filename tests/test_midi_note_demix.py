"""Regression coverage for in-place note demixing across all MIDI channels."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))

from midi import Event, MidiError, Song, Track
from midi_drum_demix import demix_drums_by_note


def signature(song):
    return sorted(
        (e.tick, e.status, e.meta_type, e.data)
        for track in song.tracks for e in track.events
        if not (e.status == 0xff and e.meta_type in (0x03, 0x2f))
    )


class NoteDemixTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(0, 480, [Track([
            Event(0, 0xff, b"Mixed", 3, 0),
            Event(0, 0xff, b"\x07\xa1\x20", 0x51, 1),
            Event(0, 0xf0, b"\x43\x10\x4c\xf7", order=2),
            Event(0, 0x90, bytes([60, 100]), order=3),
            Event(0, 0x90, bytes([64, 80]), order=4),
            Event(0, 0x99, bytes([36, 110]), order=5),
            Event(0, 0x9a, bytes([42, 100]), order=6),
            Event(120, 0xa0, bytes([60, 40]), order=7),
            Event(240, 0x80, bytes([60, 0]), order=8),
            Event(240, 0x90, bytes([64, 0]), order=9),
            Event(240, 0x89, bytes([36, 0]), order=10),
            Event(240, 0x8a, bytes([42, 0]), order=11),
            Event(240, 0xb0, bytes([7, 100]), order=12),
            Event(240, 0xff, b"", 0x2f, 13),
        ])])

    def test_all_channels_separate_channel_pitch_pairs(self):
        out, count = demix_drums_by_note(self.song)
        self.assertEqual(out.fmt, 1)
        self.assertEqual(count, 4)
        self.assertEqual(len(out.tracks), 5)
        groups = [
            {(e.status & 15, e.data[0]) for e in t.events
             if (e.status & 0xf0) in (0x80, 0x90, 0xa0)}
            for t in out.tracks
        ]
        self.assertEqual(groups, [set(), {(0, 60)}, {(0, 64)}, {(9, 36)}, {(10, 42)}])

    def test_roundtrip_preserves_events_and_source(self):
        before = self.song.to_bytes()
        out, _ = demix_drums_by_note(self.song)
        self.assertEqual(self.song.to_bytes(), before)
        self.assertEqual(signature(out), signature(self.song))
        self.assertEqual(signature(Song.from_bytes(out.to_bytes())), signature(self.song))

    def test_selected_channel_only(self):
        out, count = demix_drums_by_note(self.song, {9})
        self.assertEqual(count, 1)
        self.assertEqual(len(out.tracks), 2)
        self.assertEqual(signature(out), signature(self.song))

    def test_preserves_header_and_extra_chunks(self):
        self.song.header_extra = b"\x01\x02"
        self.song.extra_chunks = [(0, b"PRE!", b"abc"), (1, b"POST", b"def")]
        out, _ = demix_drums_by_note(self.song)
        self.assertEqual(out.extra_chunks, [(0, b"PRE!", b"abc"), (5, b"POST", b"def")])
        self.assertEqual(Song.from_bytes(out.to_bytes()).header_extra, b"\x01\x02")

    def test_rejects_invalid_channels_and_type2(self):
        for channels in (set(), {-1}, {16}, {1.5}, {"10"}):
            with self.subTest(channels=channels):
                with self.assertRaises(ValueError):
                    demix_drums_by_note(self.song, channels)
        with self.assertRaises(MidiError):
            demix_drums_by_note(Song(2, 480, [Track([])]))

    def test_no_matching_notes_keeps_track(self):
        out, count = demix_drums_by_note(self.song, {15})
        self.assertEqual(count, 0)
        self.assertEqual(len(out.tracks), 1)
        self.assertEqual(signature(out), signature(self.song))

    def test_all_sixteen_channels(self):
        events = []
        for ch in range(16):
            events.extend([Event(0, 0x90 | ch, bytes([36, 90])),
                           Event(120, 0x80 | ch, bytes([36, 0]))])
        out, count = demix_drums_by_note(Song(0, 480, [Track(events)]))
        self.assertEqual(count, 16)
        self.assertEqual(len(out.tracks), 16)


if __name__ == "__main__":
    unittest.main()
