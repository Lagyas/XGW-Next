import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from shared_note_selection import SharedNoteSelection, reconcile_editor_pairs

class Event:
    def __init__(self, uid): self.uid = uid

def note(a, b): return (0, 120, 60, 100, 90, a, b)

def test_selection_follows_reordered_events():
    old = [Event("a"), Event("b"), Event("c"), Event("d")]
    shared = SharedNoteSelection()
    shared.set(0, [(0, 1)], old)
    reordered = [old[2], old[3], old[0], old[1]]
    assert reconcile_editor_pairs({(0, 1)}, [note(0, 1), note(2, 3)], reordered, shared, 0) == {(2, 3)}

def test_deleted_selection_does_not_jump_to_another_note():
    old = [Event("a"), Event("b"), Event("c"), Event("d")]
    shared = SharedNoteSelection()
    shared.set(0, [(0, 1)], old)
    assert reconcile_editor_pairs({(0, 1)}, [note(0, 1)], old[2:], shared, 0) == set()

def test_local_selection_without_shared_identity():
    assert reconcile_editor_pairs({(0, 1), (7, 8)}, [note(0, 1)], [], None, 0) == {(0, 1)}

def test_other_track_uses_local_selection():
    shared = SharedNoteSelection()
    shared.set(1, [(0, 1)], [Event("a"), Event("b")])
    assert reconcile_editor_pairs({(2, 3)}, [note(2, 3)], [], shared, 0) == {(2, 3)}
