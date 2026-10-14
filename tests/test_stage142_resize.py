from types import SimpleNamespace
import pytest
from clip_resize import resize_clip_right
from midi import Event, MidiError


def song():
    events = [Event(0, 0x90, bytes((60, 90)), order=0),
              Event(480, 0x80, bytes((60, 0)), order=1),
              Event(0, 0xb0, bytes((7, 100)), order=2)]
    return SimpleNamespace(division=480, tracks=[SimpleNamespace(events=events)], dirty=False)


def test_shrink_note_and_preserve_controller():
    s = song()
    assert resize_clip_right(s, 0, 0, 240) == 1
    assert [e.tick for e in s.tracks[0].events] == [0, 240, 0]
    assert s.dirty


def test_extend_note():
    s = song()
    assert resize_clip_right(s, 0, 0, 960) == 1
    assert s.tracks[0].events[1].tick == 960


def test_invalid_resize_is_atomic():
    s = song()
    with pytest.raises(MidiError):
        resize_clip_right(s, 0, 0, 0)
    assert s.tracks[0].events[1].tick == 480
    assert not s.dirty
