"""Regression coverage for atomic Piano Roll duplication and view updates."""
from unittest.mock import Mock, patch
from midi import Event
from piano_roll import PianoRoll
from test_stage227_piano_gui_nudge import PianoGuiNudgeTests


def test_duplicate_commits_once_and_refreshes_views():
    editor = PianoGuiNudgeTests().make_editor()
    editor.selected_pairs = {(0, 1)}
    assert PianoRoll.duplicate_selected(editor) == 'break'
    assert len(editor.app.song.tracks[0].events) == 4
    assert editor.app.song.tracks[0].events[2].tick == 600
    editor.app.snapshot.assert_called_once()
    editor.app.notify_midi_editors.assert_called_once_with(origin=editor)
    editor.publish_note_selection.assert_called_once()


def test_invalid_duplicate_does_not_checkpoint_or_mutate():
    editor = PianoGuiNudgeTests().make_editor()
    editor.selected_pairs = {(0, 1)}
    editor.app.song.tracks[0].events[1].tick = 0x0fffffff
    original = [(e.tick, e.data) for e in editor.app.song.tracks[0].events]
    with patch('piano_roll.messagebox.showerror') as error:
        assert PianoRoll.duplicate_selected(editor) == 'break'
    error.assert_called_once()
    editor.app.snapshot.assert_not_called()
    assert [(e.tick, e.data) for e in editor.app.song.tracks[0].events] == original


def test_duplicate_without_selection_is_noop():
    editor = PianoGuiNudgeTests().make_editor()
    editor.selected_note_pairs.return_value = []
    assert PianoRoll.duplicate_selected(editor) == 'break'
    editor.app.snapshot.assert_not_called()
