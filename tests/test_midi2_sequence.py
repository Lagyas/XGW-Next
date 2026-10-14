import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import MidiError
from midi2_ump import UmpPacket, midi2_note_on, midi2_note_off
from midi2_sequence import Midi2Sequence, TimedUmpEvent


class Midi2SequenceTests(unittest.TestCase):
    def test_insert_and_pair_full_precision(self):
        sequence = Midi2Sequence()
        pair = sequence.insert_note(100, 400, 2, 5, 60, 50000, 12345, 1, 0xabcd)
        self.assertEqual(pair, (0, 1))
        note = sequence.notes()[0]
        self.assertEqual((note.start, note.end, note.group, note.channel, note.pitch),
                         (100, 400, 2, 5, 60))
        self.assertEqual((note.velocity, note.release_velocity), (50000, 12345))
        self.assertEqual((note.on_attribute_type, note.on_attribute_data), (1, 0xabcd))
        self.assertTrue(sequence.dirty)

    def test_edit_preserves_attributes_and_release_velocity(self):
        sequence = Midi2Sequence()
        pair = sequence.insert_note(100, 400, 2, 5, 60, 50000, 12345, 1, 0xabcd)
        self.assertTrue(sequence.edit_note(*pair, start=200, end=600, pitch=64, velocity=60000))
        note = sequence.notes()[0]
        self.assertEqual((note.start, note.end, note.pitch, note.velocity), (200, 600, 64, 60000))
        self.assertEqual((note.release_velocity, note.on_attribute_data), (12345, 0xabcd))

    def test_noop_edit_does_not_mark_dirty(self):
        sequence = Midi2Sequence()
        pair = sequence.insert_note(100, 400, 0, 0, 60, 30000)
        sequence.dirty = False
        self.assertFalse(sequence.edit_note(*pair))
        self.assertFalse(sequence.dirty)

    def test_invalid_edit_is_atomic(self):
        sequence = Midi2Sequence()
        pair = sequence.insert_note(100, 400, 0, 0, 60, 30000)
        original = list(sequence.events)
        sequence.dirty = False
        for values in ({"end": 50}, {"pitch": 128}, {"velocity": 65536},
                       {"start": True}, {"release_velocity": -1}):
            with self.assertRaises(MidiError):
                sequence.edit_note(*pair, **values)
            self.assertEqual(sequence.events, original)
            self.assertFalse(sequence.dirty)

    def test_delete_pair_preserves_other_events(self):
        sequence = Midi2Sequence()
        pair = sequence.insert_note(100, 400, 0, 0, 60, 30000)
        other = TimedUmpEvent(250, UmpPacket((0x20903c64,)))
        sequence.events.append(other)
        sequence.delete_note(*pair)
        self.assertEqual(sequence.events, [other])
        with self.assertRaises(MidiError):
            sequence.delete_note(*pair)

    def test_fifo_pairing_and_group_isolation(self):
        sequence = Midi2Sequence()
        sequence.insert_note(10, 100, 0, 0, 60, 10000)
        sequence.insert_note(20, 110, 0, 0, 60, 20000)
        sequence.insert_note(30, 120, 1, 0, 60, 30000)
        self.assertEqual([(n.on_index, n.off_index) for n in sequence.notes()],
                         [(0, 1), (2, 3), (4, 5)])

    def test_orphans_are_not_editable_notes(self):
        sequence = Midi2Sequence([TimedUmpEvent(0, midi2_note_on(0, 0, 60, 1000))])
        self.assertEqual(sequence.notes(), [])
        with self.assertRaises(MidiError):
            sequence.edit_note(0, 1, pitch=62)

    def test_reject_invalid_timed_event(self):
        for tick in (-1, 0x10000000, True):
            with self.assertRaises(MidiError):
                TimedUmpEvent(tick, midi2_note_off(0, 0, 60))
        with self.assertRaises(MidiError):
            TimedUmpEvent(0, b'raw')


if __name__ == '__main__':
    unittest.main()

class Midi2SequenceOperationsTests(unittest.TestCase):
    def test_quantize_selected_preserves_duration(self):
        from midi2_sequence import quantize_midi2_notes
        sequence = Midi2Sequence()
        first = sequence.insert_note(115, 315, 0, 0, 60, 30000)
        second = sequence.insert_note(245, 445, 0, 0, 64, 40000)
        sequence.dirty = False
        self.assertEqual(quantize_midi2_notes(sequence, [first], 120), 1)
        notes = sequence.notes()
        self.assertEqual((notes[0].start, notes[0].end), (120, 320))
        self.assertEqual((notes[1].start, notes[1].end), (245, 445))
        self.assertTrue(sequence.dirty)

    def test_quantize_invalid_selection_is_atomic(self):
        from midi2_sequence import quantize_midi2_notes
        sequence = Midi2Sequence()
        first = sequence.insert_note(115, 315, 0, 0, 60, 30000)
        original = list(sequence.events)
        sequence.dirty = False
        with self.assertRaises(MidiError):
            quantize_midi2_notes(sequence, [first, (5, 6)], 120)
        self.assertEqual(sequence.events, original)
        self.assertFalse(sequence.dirty)

    def test_quantize_strength(self):
        from midi2_sequence import quantize_midi2_notes
        sequence = Midi2Sequence()
        pair = sequence.insert_note(90, 190, 0, 0, 60, 30000)
        self.assertEqual(quantize_midi2_notes(sequence, [pair], 120, 50), 1)
        self.assertEqual((sequence.notes()[0].start, sequence.notes()[0].end), (105, 205))

    def test_strict_import_rejects_meta(self):
        from midi import Event, Track
        from midi2_sequence import import_midi1_track, import_midi1_channel_events
        track = Track([Event(0, 0x90, bytes((60, 100))),
                       Event(100, 0x80, bytes((60, 0))),
                       Event(100, 0xff, b'', 0x2f)])
        with self.assertRaises(MidiError):
            import_midi1_track(track)
        sequence = import_midi1_channel_events(track)
        self.assertEqual(len(sequence.events), 2)
        self.assertEqual(sequence.notes()[0].velocity, 51603)
        self.assertFalse(sequence.dirty)

    def test_strict_import_channel_only(self):
        from midi import Event, Track
        from midi2_sequence import import_midi1_track
        track = Track([Event(0, 0x90, bytes((60, 127))),
                       Event(100, 0x80, bytes((60, 64)))])
        sequence = import_midi1_track(track, 4)
        self.assertEqual(sequence.notes()[0].group, 4)
        self.assertEqual(sequence.notes()[0].velocity, 65535)

class Midi2PairingSafetyTests(unittest.TestCase):
    def test_edit_rejects_pairing_change(self):
        sequence = Midi2Sequence()
        first = sequence.insert_note(100, 200, 0, 0, 60, 10000)
        sequence.insert_note(150, 250, 0, 0, 60, 20000)
        before = list(sequence.events)
        sequence.dirty = False
        with self.assertRaises(MidiError):
            sequence.edit_note(*first, end=260)
        self.assertEqual(sequence.events, before)
        self.assertFalse(sequence.dirty)
