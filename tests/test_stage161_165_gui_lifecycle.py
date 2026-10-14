"""Headless Windows GUI lifecycle regression checks (no display needed)."""
from unittest.mock import Mock
import tkinter as tk
from piano_roll import PianoRoll
from app import App


def test_piano_roll_close_cancels_pending_timer():
    window = Mock()
    window._playhead_timer = 'timer-1'
    PianoRoll.close_editor(window)
    window.after_cancel.assert_called_once_with('timer-1')
    window.destroy.assert_called_once()
    assert window._playhead_timer is None


def test_piano_roll_poll_does_not_reschedule_destroyed_window():
    window = Mock()
    window.winfo_exists.return_value = False
    PianoRoll._poll_playhead(window)
    window.after.assert_not_called()
    assert window._playhead_timer is None


def test_piano_roll_poll_reschedules_live_window():
    window = Mock()
    window.winfo_exists.return_value = True
    window.after.return_value = 'timer-2'
    PianoRoll._poll_playhead(window)
    window.update_playhead.assert_called_once()
    assert window._playhead_timer == 'timer-2'


def test_piano_roll_undo_returns_break():
    window = Mock()
    window.app.history = [object()]
    assert PianoRoll.undo_note_edit(window) == 'break'
    window.app.undo.assert_called_once()


def test_piano_roll_redo_returns_break():
    window = Mock()
    window.app.redo_history = [object()]
    assert PianoRoll.redo_note_edit(window) == 'break'
    window.app.redo.assert_called_once()


def test_app_playhead_does_not_reschedule_while_closing():
    app = Mock()
    app._closing = True
    app.song = None
    app.playhead_tick = 0
    app.transport_window = None
    App._update_playhead(app)
    app.root.after.assert_not_called()
