import pytest
from midi import MidiError
from shared_note_selection import SharedNoteSelection


def note(a, b):
    return (0, 120, 60, 10, 90, a, b)


def test_selection_is_track_scoped():
    s = SharedNoteSelection()
    s.set(1, [(3, 4)])
    assert s.get(1, [note(3, 4), note(5, 6)]) == {(3, 4)}
    assert s.get(2, [note(3, 4)]) == set()


def test_stale_pairs_are_ignored():
    s = SharedNoteSelection()
    s.set(0, [(3, 4)])
    assert s.get(0, [note(5, 6)]) == set()


def test_clear_and_replace():
    s = SharedNoteSelection()
    s.set(0, [(3, 4), (3, 4)])
    s.set(0, [(5, 6)])
    assert s.get(0, [note(3, 4), note(5, 6)]) == {(5, 6)}
    s.clear()
    assert s.get(0, [note(5, 6)]) == set()


@pytest.mark.parametrize('pairs', [[(1, 1)], [(True, 2)], [(-1, 2)], [(1,)], [(1, '2')]])
def test_invalid_pair_rejected_without_mutation(pairs):
    s = SharedNoteSelection()
    s.set(0, [(3, 4)])
    with pytest.raises(MidiError):
        s.set(0, pairs)
    assert s.get(0, [note(3, 4)]) == {(3, 4)}
