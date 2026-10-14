import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from drum_editor import DrumEditor

class FakeSelection:
    def __init__(self, hits, selected=None):
        self.selected_hits = set(hits)
        self.selected = selected
        self.notes = [(0, 120, 36, 10, 100, 0, 1)] * 3
        self._selection_info = lambda: None
        self.render = lambda: None
        self.hit_at = lambda event: event

class DrumSelectionTests(unittest.TestCase):
    def test_ctrl_toggle_add_and_remove(self):
        fake = FakeSelection({0}, 0)
        self.assertEqual(DrumEditor.toggle_selection(fake, 1), 'break')
        self.assertEqual(fake.selected_hits, {0, 1})
        DrumEditor.toggle_selection(fake, 0)
        self.assertEqual(fake.selected_hits, {1})

    def test_select_all_and_clear(self):
        fake = FakeSelection(set())
        DrumEditor.select_all_hits(fake)
        self.assertEqual(fake.selected_hits, {0, 1, 2})
        DrumEditor.clear_selection(fake)
        self.assertEqual(fake.selected_hits, set())
        self.assertIsNone(fake.selected)

    def test_normal_click_replaces_selection(self):
        fake = FakeSelection({0, 1}, 0)
        DrumEditor.select(fake, 2)
        self.assertEqual(fake.selected_hits, {2})
