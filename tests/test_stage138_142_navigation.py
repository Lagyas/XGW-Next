from sequencer_view import zoom_anchor_tick, clip_edge_hit, update_clip_selection


def test_zoom_anchor_matches_tick_at_mouse():
    assert zoom_anchor_tick(230 + 56, 480, 28) == 960
    assert zoom_anchor_tick(100, 480, 28) == 0


def test_zoom_anchor_rejects_invalid_division():
    assert zoom_anchor_tick(300, 0, 28) == 0
    assert zoom_anchor_tick(300, 0xE728, 28) == 0


def test_clip_edge_is_not_body():
    assert clip_edge_hit(950, 0, 960, 480, 28)
    assert not clip_edge_hit(100, 0, 960, 480, 28)
    assert not clip_edge_hit(961, 0, 960, 480, 28)


def test_ctrl_selection_keeps_other_clips():
    assert update_clip_selection({(0, 0)}, (1, 0), ctrl=True) == {(0, 0), (1, 0)}
