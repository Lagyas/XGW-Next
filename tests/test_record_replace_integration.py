"""Regression tests for Punch/Replace data placement."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import pytest
from midi import Event, Track, MidiError
from recording_ops import replace_take_range


def test_replace_only_selected_channel_and_range():
    old = Track([Event(10, 0x90, b'\x3c\x40'), Event(10, 0x91, b'\x3d\x40'),
                 Event(20, 0x90, b'\x3c\x00'), Event(20, 0xff, b'tempo', 1),
                 Event(50, 0x90, b'\x40\x40')])
    take = Track([Event(12, 0x90, b'\x43\x40')])
    result = replace_take_range(old, take, 0, 30, channels={0})
    assert [(e.tick, e.status) for e in result.events] == [(10, 0x91), (12, 0x90), (20, 0xff), (50, 0x90)]
    assert len(old.events) == 5


def test_replace_rejects_outside_punch():
    with pytest.raises(MidiError):
        replace_take_range(Track(), Track([Event(30, 0x90, b'\x3c\x40')]), 0, 30)


def test_replace_preserves_retained_identity():
    retained = Event(40, 0x90, b'\x40\x40')
    result = replace_take_range(Track([retained]), Track(), 0, 30)
    assert result.events[0].uid == retained.uid
