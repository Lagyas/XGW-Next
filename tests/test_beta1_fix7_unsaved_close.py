"""Beta 1 Fix 7: ask to save unsaved changes before closing or opening."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

import app as app_module
from app import App


def _app(dirty=True, path="song.mid"):
    a = SimpleNamespace(song=object(), path=path)
    a.has_unsaved_changes = lambda: dirty
    a.save_as = Mock(return_value=True)
    a.save_project = Mock(return_value=True)
    return a


def test_clean_document_closes_without_asking():
    a = _app(dirty=False)
    with patch.object(app_module.messagebox, "askyesnocancel") as ask:
        assert App.confirm_discard_changes(a) is True
        ask.assert_not_called()


def test_cancel_keeps_the_document_open():
    a = _app()
    with patch.object(app_module.messagebox, "askyesnocancel", return_value=None):
        assert App.confirm_discard_changes(a) is False
    a.save_as.assert_not_called()


def test_dont_save_continues_and_drops_recovery():
    a = _app()
    with patch.object(app_module.messagebox, "askyesnocancel", return_value=False), \
         patch("project_recovery.discard_recovery") as discard:
        assert App.confirm_discard_changes(a) is True
        discard.assert_called_once_with("song.mid")
    a.save_as.assert_not_called()


def test_save_uses_midi_or_project_save_and_respects_failure():
    a = _app()
    with patch.object(app_module.messagebox, "askyesnocancel", return_value=True):
        assert App.confirm_discard_changes(a) is True
        a.save_as.assert_called_once_with()
        a.save_as.return_value = False
        assert App.confirm_discard_changes(a) is False
    p = _app(path="project.xgwn")
    with patch.object(app_module.messagebox, "askyesnocancel", return_value=True):
        assert App.confirm_discard_changes(p) is True
        p.save_project.assert_called_once_with()


def test_close_app_stops_when_cancelled():
    a = SimpleNamespace(_closing=False)
    a.confirm_discard_changes = Mock(return_value=False)
    a.workspace = Mock()
    App.close_app(a)
    assert a._closing is False
    a.workspace.close_all.assert_not_called()


def test_unsaved_detection_uses_saved_fingerprint():
    a = SimpleNamespace(song=object(), _saved_fingerprint=b"x")
    a._document_fingerprint = lambda: b"x"
    assert App.has_unsaved_changes(a) is False
    a._document_fingerprint = lambda: b"y"
    assert App.has_unsaved_changes(a) is True
    a.song = None
    assert App.has_unsaved_changes(a) is False
