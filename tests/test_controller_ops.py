import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, Track, Event, MidiError
from controller_ops import controller_events, set_controller, delete_controller

class ControllerOpsTests(unittest.TestCase):
    def setUp(self):
        self.song = Song(0, 480, [Track([
            Event(0, 0x90, bytes((60, 100)), order=0),
            Event(240, 0x80, bytes((60, 0)), order=1),
            Event(0, 0xff, b"", 0x2f, 2),
        ])])

    def test_insert_update_delete_and_roundtrip(self):
        index = set_controller(self.song, 0, 2, 91, 120, 80)
        found = controller_events(self.song, 0, 2, 91)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][0], index)
        set_controller(self.song, 0, 2, 93, 160, 55, event_index=index)
        restored = Song.from_bytes(self.song.to_bytes())
        self.assertEqual([(e.tick, e.data) for _, e in controller_events(restored, 0, 2, 93)],
                         [(160, bytes((93, 55)))])
        delete_controller(self.song, 0, index)
        self.assertEqual(controller_events(self.song, 0), [])

    def test_invalid_values_do_not_mutate(self):
        before = len(self.song.tracks[0].events)
        with self.assertRaises(MidiError):
            set_controller(self.song, 0, 1, 7, 0, 128)
        self.assertEqual(len(self.song.tracks[0].events), before)

    def test_refuse_edit_of_note_event(self):
        with self.assertRaises(MidiError):
            set_controller(self.song, 0, 1, 7, 0, 100, event_index=0)
        with self.assertRaises(MidiError):
            delete_controller(self.song, 0, 0)

    def test_filter_by_channel_and_controller(self):
        set_controller(self.song, 0, 1, 7, 0, 90)
        set_controller(self.song, 0, 2, 7, 120, 70)
        set_controller(self.song, 0, 2, 10, 240, 64)
        self.assertEqual(len(controller_events(self.song, 0, 2, 7)), 1)
        self.assertEqual(len(controller_events(self.song, 0, 2)), 2)

if __name__ == "__main__":
    unittest.main()
