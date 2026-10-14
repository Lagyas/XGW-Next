import pytest
from midi import Song, Track, Event, MidiError
from integration_ops import move_events, transfer_events
from program_ops import set_patch
from transport_integration import normalized_seek, clamp_note_range
from midi_compat import audit_roundtrip

def song():
    return Song(1, 480, [Track([Event(10, 0x90, b'\x3c\x64'), Event(100, 0x80, b'\x3c\x00'), Event(120, 0xff, b'', 0x2f)]), Track([])])

def test_move_note_pair():
    s = song()
    assert move_events(s, 0, [0,1], 20, 2) == 2
    assert [(e.tick,e.data[0]) for e in s.tracks[0].events[:2]] == [(30,62),(120,62)]
    assert audit_roundtrip(s)

def test_atomic_pitch_overflow():
    s = song()
    s.tracks[0].events[1].data = b'\x7f\x00'
    with pytest.raises(MidiError): move_events(s, 0, [0,1], 1, 1)
    assert s.tracks[0].events[0].tick == 10
    assert not s.dirty

def test_copy_new_identity():
    s = song()
    move_events(s, 0, [0], 20, copy=True)
    assert s.tracks[0].events[-1].uid != s.tracks[0].events[0].uid
    assert s.tracks[0].events[-1].tick == 30

def test_transfer_and_undo_ready():
    s = song()
    transfer_events(s, 0, [0,1], 1, 5)
    assert len(s.tracks[0].events) == 1
    assert len(s.tracks[1].events) == 2
    assert audit_roundtrip(s)

def test_transfer_atomic_invalid():
    s = song()
    with pytest.raises(MidiError): transfer_events(s, 0, [0,2], 1)
    assert len(s.tracks[0].events) == 3 and not s.tracks[1].events

def test_patch_order_and_preservation():
    s = song()
    set_patch(s, 0, 1, 40, 63, 2)
    patch = s.tracks[0].events[-3:]
    assert [(e.status,e.data) for e in patch] == [(0xb0,b'\x00\x3f'),(0xb0,b'\x20\x02'),(0xc0,b'\x28')]
    assert audit_roundtrip(s)

def test_patch_invalid_atomic():
    s = song()
    with pytest.raises(MidiError): set_patch(s, 0, 1, 8, 128)
    assert not s.dirty

def test_seek_policy():
    assert normalized_seek(120,loop=True,left=20,right=100) == 20
    assert normalized_seek(10,loop=True,left=20,right=100) == 10
    assert normalized_seek(120) == 120

def test_duration_limits():
    assert clamp_note_range(10,20) == (10,30)
    with pytest.raises(MidiError): clamp_note_range(10,0)
