import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from project_bundle import save_project, load_project_workspace, load_project, validate_workspace

class WorkspaceBundleTests(unittest.TestCase):
    def song(self):
        return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64'), Event(480, 0x80, b'\x3c\x00')])])

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'test.xgwn'
            state = {'geometry': {'Piano Roll': '800x500+10+20'}, 'open_editors': ['Piano Roll'], 'playhead_tick': 100, 'loop_start': 20, 'loop_end': 400}
            save_project(path, self.song(), workspace=state)
            self.assertEqual(load_project_workspace(path), state)
            self.assertIsNotNone(load_project(path)[0])

    def test_old_project_is_supported(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'old.xgwn'
            save_project(path, self.song())
            self.assertIsNone(load_project_workspace(path))

    def test_invalid_window_rejected(self):
        with self.assertRaises(MidiError):
            validate_workspace({'geometry': {'Unknown': '800x500+0+0'}})

    def test_duplicate_editor_rejected(self):
        with self.assertRaises(MidiError):
            validate_workspace({'open_editors': ['Piano Roll', 'Piano Roll']})

    def test_negative_position_rejected(self):
        with self.assertRaises(MidiError):
            validate_workspace({'playhead_tick': -1})
