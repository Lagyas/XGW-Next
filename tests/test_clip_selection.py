from sequencer_view import update_clip_selection


def test_replace_selection():
    assert update_clip_selection({(0, 0), (1, 1)}, (2, 3)) == {(2, 3)}


def test_ctrl_toggle_on():
    assert update_clip_selection({(0, 0)}, (1, 2), ctrl=True) == {(0, 0), (1, 2)}


def test_ctrl_toggle_off():
    assert update_clip_selection({(0, 0), (1, 2)}, (1, 2), ctrl=True) == {(0, 0)}


def test_shift_range():
    assert update_clip_selection({(0, 2)}, (0, 5), shift=True) == {(0, 2), (0, 3), (0, 4), (0, 5)}


def test_shift_without_same_track_replaces():
    assert update_clip_selection({(0, 2)}, (1, 4), shift=True) == {(1, 4)}
