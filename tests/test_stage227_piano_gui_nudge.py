"""Headless GUI-contract tests for Piano Roll keyboard note edits."""
import unittest
from unittest.mock import Mock
from midi import Song, Track, Event
from piano_roll import PianoRoll


class PianoGuiNudgeTests(unittest.TestCase):
    def make_editor(self):
        song = Song(1, 480, [Track([
            Event(120, 0x90, bytes([60, 90]), order=0),
            Event(360, 0x80, bytes([60, 0]), order=1),
        ])])
        editor = object.__new__(PianoRoll)
        editor.app = Mock()
        editor.app.song = song
        editor.track_index = 0
        editor.snap_option = Mock()
        editor.snap_option.get.return_value = '1/16'
        editor.selected_note_pairs = Mock(return_value=[(0, 1)])
        editor.render = Mock()
        editor.publish_note_selection = Mock()
        editor.info = Mock()
        return editor

    def test_move_notifies_all_views_once(self):
        editor = self.make_editor()
        self.assertEqual(PianoRoll.nudge_selected_notes(editor, pitch=1), 'break')
        self.assertEqual(editor.app.song.tracks[0].events[0].data[0], 61)
        editor.app.snapshot.assert_called_once()
        editor.app.show_events.assert_called_once()
        editor.app.notify_midi_editors.assert_called_once_with(origin=editor)
        editor.publish_note_selection.assert_called_once()

    def test_zero_delta_is_not_undoable(self):
        editor = self.make_editor()
        self.assertEqual(PianoRoll.nudge_selected_notes(editor), 'break')
        editor.app.snapshot.assert_not_called()
        editor.app.show_events.assert_not_called()

    def test_empty_selection_is_not_undoable(self):
        editor = self.make_editor()
        editor.selected_note_pairs.return_value = []
        self.assertEqual(PianoRoll.nudge_selected_notes(editor, steps=1), 'break')
        editor.app.snapshot.assert_not_called()


if __name__ == '__main__':
    unittest.main()
