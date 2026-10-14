from shared_note_selection import SharedNoteSelection


def test_reconcile_drops_deleted_pairs():
    state = SharedNoteSelection()
    state.set(0, [(1, 2), (3, 4)])
    assert state.reconcile(0, [(0, 10, 60, 1, 90, 3, 4)]) == {(3, 4)}
    assert state.pairs == frozenset({(3, 4)})


def test_reconcile_other_track_does_not_modify():
    state = SharedNoteSelection()
    state.set(0, [(1, 2)])
    assert state.reconcile(1, []) == set()
    assert state.get(0, [(0, 10, 60, 1, 90, 1, 2)]) == {(1, 2)}


def test_reconcile_empty_selection():
    state = SharedNoteSelection()
    assert state.reconcile(0, []) == set()
    state.set(0, [])
    assert state.reconcile(0, []) == set()
