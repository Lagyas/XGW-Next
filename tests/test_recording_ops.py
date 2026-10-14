import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Event, Track, Song, MidiError
from recording_ops import merge_take

class OverdubTests(unittest.TestCase):
    def test_overlay_preserves_existing_and_order(self):
        original = Track([Event(0, 0xff, b'Piano', 3, 0),
                          Event(120, 0x90, b'\x3c\x40', order=1),
                          Event(240, 0x80, b'\x3c\x00', order=2)])
        take = Track([Event(120, 0x90, b'\x40\x64'), Event(300, 0x80, b'\x40\x00')])
        result = merge_take(original, take)
        self.assertEqual([(e.tick, e.status) for e in result.events],
                         [(0, 255), (120, 144), (120, 144), (240, 128), (300, 128)])
        self.assertEqual(len(original.events), 3)
        self.assertEqual([e.order for e in result.events], list(range(5)))

    def test_end_of_track_and_roundtrip(self):
        original = Track([Event(0, 0xff, b'Piano', 3), Event(100, 0xff, b'', 0x2f)])
        merged = merge_take(original, Track([Event(400, 0x90, b'\x3c\x50')]))
        song = Song(0, 480, [merged]); song.dirty = True
        parsed = Song.from_bytes(song.to_bytes())
        self.assertEqual(parsed.tracks[0].events[-1].tick, 400)
        self.assertEqual(parsed.tracks[0].events[-1].meta_type, 0x2f)

    def test_reject_non_channel_and_invalid_ticks(self):
        with self.assertRaises(MidiError):
            merge_take(Track(), Track([Event(0, 0xff, b'', 1)]))
        with self.assertRaises(MidiError):
            merge_take(Track(), Track([Event(-1, 0x90, b'\x3c\x50')]))

if __name__ == '__main__': unittest.main()

class RecordingQuantizeTests(unittest.TestCase):
    def test_onset_and_note_off_move_together(self):
        from recording_ops import quantize_take_onsets
        take = Track([Event(117, 0x90, b'\x3c\x60'), Event(201, 0x80, b'\x3c\x00')])
        result = quantize_take_onsets(take, 120)
        self.assertEqual([e.tick for e in result.events], [120, 204])
        self.assertEqual([e.tick for e in take.events], [117, 201])

    def test_controller_is_not_quantized(self):
        from recording_ops import quantize_take_onsets
        take = Track([Event(110, 0x90, b'\x3c\x60'), Event(115, 0xb0, b'\x07\x40'),
                      Event(230, 0x90, b'\x3c\x00')])
        result = quantize_take_onsets(take, 120)
        self.assertEqual([(e.tick, e.status) for e in result.events],
                         [(115, 0xb0), (120, 0x90), (240, 0x90)])

    def test_overlapping_same_pitch_fifo_pairs(self):
        from recording_ops import quantize_take_onsets
        take = Track([Event(100, 0x90, b'\x3c\x50'), Event(130, 0x90, b'\x3c\x60'),
                      Event(200, 0x80, b'\x3c\x00'), Event(230, 0x80, b'\x3c\x00')])
        result = quantize_take_onsets(take, 120)
        self.assertEqual(sorted(e.tick for e in result.events), [120, 120, 220, 220])

    def test_unpaired_off_and_disabled_grid(self):
        from recording_ops import quantize_take_onsets
        take = Track([Event(13, 0x80, b'\x3c\x00')])
        self.assertEqual(quantize_take_onsets(take, 120).events[0].tick, 13)
        self.assertEqual(quantize_take_onsets(take, 0).events[0].tick, 13)

    def test_invalid_grid(self):
        from recording_ops import quantize_take_onsets
        for grid in (-1, True, 1.5, 0x10000000):
            with self.assertRaises(MidiError):
                quantize_take_onsets(Track(), grid)


class RecordingQuantizeStrengthTests(unittest.TestCase):
    def test_half_strength_preserves_duration(self):
        from recording_ops import quantize_take_onsets
        take = Track([Event(100, 0x90, b'\x3c\x50'),
                      Event(180, 0x80, b'\x3c\x00')])
        result = quantize_take_onsets(take, 120, strength=50)
        self.assertEqual([e.tick for e in result.events], [110, 190])

    def test_zero_strength_does_not_change_events(self):
        from recording_ops import quantize_take_onsets
        take = Track([Event(100, 0x90, b'\x3c\x50')])
        self.assertEqual(quantize_take_onsets(take, 120, strength=0).events[0].tick, 100)

    def test_invalid_strength(self):
        from recording_ops import quantize_take_onsets
        for strength in (-1, 101, 1.5, True):
            with self.assertRaises(MidiError):
                quantize_take_onsets(Track(), 120, strength=strength)


class RecordingIdentityTests(unittest.TestCase):
    def test_overdub_preserves_both_existing_and_take_identities(self):
        original = Track([Event(0, 0x90, b'\x3c\x50')])
        take = Track([Event(20, 0x80, b'\x3c\x00')])
        result = merge_take(original, take)
        self.assertEqual({e.uid for e in result.events}, {original.events[0].uid, take.events[0].uid})
        self.assertIsNot(result.events[0], original.events[0])

    def test_quantize_preserves_event_identity(self):
        from recording_ops import quantize_take_onsets
        take = Track([Event(113, 0x90, b'\x3c\x50'), Event(200, 0x80, b'\x3c\x00')])
        result = quantize_take_onsets(take, 120)
        self.assertEqual({e.uid for e in result.events}, {e.uid for e in take.events})

    def test_overdub_rejects_duplicate_identity_without_mutation(self):
        original = Track([Event(0, 0x90, b'\x3c\x50')])
        take = Track([Event(20, 0x80, b'\x3c\x00', uid=original.events[0].uid)])
        with self.assertRaises(MidiError):
            merge_take(original, take)
        self.assertEqual(original.events[0].tick, 0)
