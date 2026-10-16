"""Regression checks for preserving Canvas items across MIDI clip clicks."""
from types import SimpleNamespace
from unittest.mock import Mock

from sequencer_view import SequencerView


def test_select_track_same_row_does_not_redraw():
    view = SimpleNamespace(selected_track=2, draw=Mock())
    SequencerView.select_track(view, 2)
    view.draw.assert_not_called()
    SequencerView.select_track(view, 3)
    view.draw.assert_called_once_with()


def test_refresh_clip_selection_updates_existing_items():
    canvas = Mock()
    canvas.find_withtag.return_value = (10, 20)
    canvas.gettags.side_effect = [
        ("midi-clip", "clip-0-0"),
        ("midi-clip", "clip-0-1"),
    ]
    view = SimpleNamespace(
        canvas=canvas, selected_clips={(0, 1)}, muted=set(), solo=set()
    )
    SequencerView._refresh_clip_selection(view)
    assert canvas.itemconfigure.call_count == 2
    assert canvas.itemconfigure.call_args_list[0].kwargs["width"] == 1
    assert canvas.itemconfigure.call_args_list[1].kwargs["width"] == 3
