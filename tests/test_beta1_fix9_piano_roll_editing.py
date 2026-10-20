"""Beta 1 Fix 9: Piano Roll note grabbing, vertical moves, copy / paste and
macOS shortcuts."""
from midi import Event, Song, Track
from piano_roll import (KEYBOARD_WIDTH, NOTE_HEIGHT, PIXELS_PER_BEAT, TOP_MARGIN, copy_notes,
                        drag_delta, extract_notes, note_at, paste_notes)

DIV = 480


def song_with(notes):
    events = []
    for tick, dur, pitch in notes:
        events.append(Event(tick, 0x90, bytes((pitch, 100))))
        events.append(Event(tick + dur, 0x80, bytes((pitch, 0))))
    events.append(Event(max(t + d for t, d, _ in notes), 0xFF, b"", 0x2F))
    return Song(1, DIV, [Track(events)])


def point(tick, pitch):
    return (KEYBOARD_WIDTH + tick / DIV * PIXELS_PER_BEAT,
            TOP_MARGIN + (127 - pitch) * NOTE_HEIGHT + NOTE_HEIGHT / 2)


def test_note_at_hits_the_note_under_the_click():
    notes = extract_notes(song_with([(0, 480, 60), (960, 60, 62)]).tracks[0])
    assert note_at(notes, DIV, *point(240, 60)) == 0
    assert note_at(notes, DIV, *point(240, 61)) is None
    # a very short note is still easy to grab (tolerance)
    x, y = point(960, 62)
    assert note_at(notes, DIV, x - 2, y) == 1
    assert note_at(notes, DIV, x + 10, y) == 1  # 8 px note + 3 px tolerance
    assert note_at(notes, DIV, x + 13, y) is None
    assert note_at(notes, DIV, 10, y) is None


def test_vertical_drag_ignores_sideways_jitter():
    assert drag_delta(6, -3 * NOTE_HEIGHT, DIV) == (0, 3)
    assert drag_delta(30, -3 * NOTE_HEIGHT, DIV)[0] > 0
    assert drag_delta(3, 0, DIV)[0] > 0
    assert drag_delta(0, NOTE_HEIGHT * 2, DIV) == (0, -2)


def test_copy_and_paste_keep_rhythm_and_pitch():
    song = song_with([(480, 240, 60), (720, 240, 64), (2000, 100, 70)])
    notes = extract_notes(song.tracks[0])
    pairs = {(n[5], n[6]) for n in notes if n[2] in (60, 64)}
    clip = copy_notes(notes, pairs)
    assert sorted(clip) == [(0, 240, 60, 100, 1), (240, 240, 64, 100, 1)]
    keys = paste_notes(song, 0, clip, 3840)
    assert sorted(keys) == [(3840, 60, 1), (4080, 64, 1)]
    after = extract_notes(song.tracks[0])
    assert len(after) == 5
    assert {(n[0], n[1] - n[0], n[2]) for n in after} >= {(3840, 240, 60), (4080, 240, 64)}


def test_paste_rejects_bad_clipboard_without_changing_the_song():
    song = song_with([(0, 100, 60)])
    before = len(song.tracks[0].events)
    import pytest
    from midi import MidiError
    with pytest.raises(MidiError):
        paste_notes(song, 0, [(0, 10, 200, 100, 1)], 0)
    with pytest.raises(MidiError):
        paste_notes(song, 0, [(0, 10, 60, 100, 1)], -1)
    assert len(song.tracks[0].events) == before


def test_shortcuts_cover_command_on_macos(monkeypatch):
    import importlib
    import sys
    import piano_roll
    monkeypatch.setattr(sys, "platform", "darwin")
    mac = importlib.reload(piano_roll)
    try:
        assert mac.SHORTCUT_MODIFIERS == ("Command", "Control")
        assert mac.RIGHT_BUTTON == 2
    finally:
        monkeypatch.setattr(sys, "platform", "win32")
        importlib.reload(piano_roll)
