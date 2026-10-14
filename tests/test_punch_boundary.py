import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import unittest
from midi import Event, Track, MidiError
from recording_ops import replace_take_range_sustain_safe

class PunchBoundaryTests(unittest.TestCase):
    def test_note_crossing_both_boundaries_is_split(self):
        src = Track([Event(10, 0x90, b'\x3c\x64'), Event(90, 0x80, b'\x3c\x00')])
        result = replace_take_range_sustain_safe(src, Track(), 30, 60)
        self.assertEqual([(e.tick, e.status) for e in result.events],
                         [(10, 0x90), (30, 0x80), (60, 0x90), (90, 0x80)])
        self.assertEqual([e.tick for e in src.events], [10, 90])

    def test_note_starting_inside_ends_after(self):
        src = Track([Event(40, 0x90, b'\x3c\x64'), Event(90, 0x80, b'\x3c\x00')])
        result = replace_take_range_sustain_safe(src, Track(), 30, 60)
        self.assertEqual([(e.tick, e.status) for e in result.events], [(60, 0x90), (90, 0x80)])

    def test_other_channel_and_meta_untouched(self):
        src = Track([Event(10, 0x91, b'\x3c\x64'), Event(90, 0x81, b'\x3c\x00'),
                     Event(35, 0xff, b'hello', 1)])
        result = replace_take_range_sustain_safe(src, Track(), 30, 60, channels={0})
        self.assertEqual({e.uid for e in result.events}, {e.uid for e in src.events})

    def test_take_wrong_channel_rejected(self):
        with self.assertRaises(MidiError):
            replace_take_range_sustain_safe(Track(), Track([Event(40, 0x91, b'\x3c\x64')]),
                                            30, 60, channels={0})

    def test_original_note_identity_retained_at_outer_edges(self):
        src = Track([Event(10, 0x90, b'\x3c\x64'), Event(90, 0x80, b'\x3c\x00')])
        result = replace_take_range_sustain_safe(src, Track(), 30, 60)
        self.assertEqual(result.events[0].uid, src.events[0].uid)
        self.assertEqual(result.events[-1].uid, src.events[-1].uid)
