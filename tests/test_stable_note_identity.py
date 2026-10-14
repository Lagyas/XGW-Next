from copy import deepcopy
from midi import Event
from shared_note_selection import SharedNoteSelection


def test_uuid_survives_deepcopy_and_reorder():
    events = [Event(0, 0x90, b'\x3c\x64'), Event(120, 0x80, b'\x3c\x00'), Event(20, 0xb0, b'\x07\x40')]
    selection = SharedNoteSelection()
    selection.set(0, [(0, 1)], events)
    copied = deepcopy(events)
    reordered = [copied[2], copied[0], copied[1]]
    assert selection.get(0, [(0, 120, 60, 1, 100, 1, 2)], reordered) == {(1, 2)}
    assert selection.reconcile(0, [(0, 120, 60, 1, 100, 1, 2)], reordered) == {(1, 2)}


def test_uuid_prevents_reusing_deleted_indices():
    original = [Event(0, 0x90, b'\x3c\x64'), Event(120, 0x80, b'\x3c\x00')]
    selection = SharedNoteSelection()
    selection.set(0, [(0, 1)], original)
    replacement = [Event(0, 0x90, b'\x40\x64'), Event(120, 0x80, b'\x40\x00')]
    assert selection.get(0, [(0, 120, 64, 1, 100, 0, 1)], replacement) == set()


def test_uuid_scope_and_no_missing_events_fallback():
    events = [Event(0, 0x90, b'\x3c\x64'), Event(120, 0x80, b'\x3c\x00')]
    selection = SharedNoteSelection()
    selection.set(2, [(0, 1)], events)
    notes = [(0, 120, 60, 1, 100, 0, 1)]
    assert selection.get(1, notes, events) == set()
    assert selection.get(2, notes) == set()


def test_event_uid_unique_and_excluded_from_value_equality():
    a, b = Event(0, 0x90, b'\x3c\x64'), Event(0, 0x90, b'\x3c\x64')
    assert a == b
    assert a.uid != b.uid
