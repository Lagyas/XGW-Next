import pytest
from midi import Track, Event, MidiError
from recording_ops import replace_take_range


def note(tick, channel=0):
    return Event(tick, 0x90 | channel, bytes([60, 90]))


def test_replace_only_inside_range():
    a, b, c = note(5), note(15), note(25)
    take = note(17)
    result = replace_take_range(Track([a,b,c]), Track([take]), 10, 20)
    assert [e.tick for e in result.events] == [5,17,25]
    assert [e.uid for e in result.events] == [a.uid,take.uid,c.uid]


def test_preserves_meta_and_other_channel():
    meta = Event(12, 0xff, b'\x07', 0x51)
    other = note(12, 2)
    result = replace_take_range(Track([meta,other,note(12)]), Track([note(13)]), 10,20,channels={0})
    assert meta.uid in [e.uid for e in result.events]
    assert other.uid in [e.uid for e in result.events]


def test_rejects_take_outside_window():
    with pytest.raises(MidiError):
        replace_take_range(Track([]), Track([note(21)]), 10, 20)


def test_rejects_invalid_range():
    with pytest.raises(MidiError):
        replace_take_range(Track([]), Track([]), 20, 10)


def test_rejects_duplicate_ids():
    n = note(15)
    with pytest.raises(MidiError):
        replace_take_range(Track([n]), Track([n]), 10, 20, channels={2})
