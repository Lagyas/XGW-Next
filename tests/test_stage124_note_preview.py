import unittest
from midi import Event, Track
from sequencer_view import clip_note_preview


class NotePreviewTests(unittest.TestCase):
    def test_note_geometry_and_pitch(self):
        track = Track([Event(0, 0x90, bytes([60, 100])),
                       Event(240, 0x80, bytes([60, 0])),
                       Event(240, 0x90, bytes([72, 100])),
                       Event(480, 0x80, bytes([72, 0]))])
        result = clip_note_preview(track, 0, 480, 480, 96)
        self.assertEqual(result, [(0, 48, 0), (48, 96, 1)])

    def test_clip_edge_and_velocity_zero(self):
        track = Track([Event(0, 0x90, bytes([64, 100])),
                       Event(480, 0x90, bytes([64, 0]))])
        self.assertEqual(clip_note_preview(track, 120, 360, 480, 96),
                         [(0, 48, 0)])

    def test_invalid_division_and_empty(self):
        self.assertEqual(clip_note_preview(Track([]), 0, 480, 480, 96), [])
        self.assertEqual(clip_note_preview(Track([]), 0, 480, 0, 96), [])

    def test_sampling_limit(self):
        events = []
        for i in range(100):
            events.extend([Event(i * 10, 0x90, bytes([60, 90])),
                           Event(i * 10 + 5, 0x80, bytes([60, 0]))])
        self.assertLessEqual(len(clip_note_preview(Track(events), 0, 1000, 480, 96, 10)), 10)


if __name__ == '__main__':
    unittest.main()
