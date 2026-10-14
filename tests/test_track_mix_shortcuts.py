import unittest
from types import SimpleNamespace
from sequencer_view import SequencerView

class TrackMixShortcutsTests(unittest.TestCase):
    def test_toggle_selected(self):
        calls = []
        fake = SimpleNamespace(song=SimpleNamespace(tracks=[1, 2]), selected_track=1,
                               on_toggle=lambda i, k: calls.append((i, k)))
        self.assertEqual(SequencerView.toggle_selected(fake, 'mute'), 'break')
        self.assertEqual(calls, [(1, 'mute')])

    def test_clear_solo(self):
        calls = []
        fake = SimpleNamespace(song=SimpleNamespace(tracks=[1, 2, 3]), solo={2, 0},
                               on_toggle=lambda i, k: calls.append((i, k)))
        self.assertEqual(SequencerView.clear_solo(fake), 'break')
        self.assertEqual(calls, [(0, 'solo'), (2, 'solo')])

    def test_shortcuts_without_song(self):
        fake = SimpleNamespace(song=None, selected_track=0, solo={0}, on_toggle=lambda *_: self.fail('called'))
        self.assertEqual(SequencerView.toggle_selected(fake, 'solo'), 'break')
        self.assertEqual(SequencerView.clear_solo(fake), 'break')
