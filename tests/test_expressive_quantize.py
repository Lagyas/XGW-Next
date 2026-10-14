import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import pytest
from midi import Song, Track, Event, MidiError
from expressive_quantize import transform

def make_song(starts=(61, 181)):
    ev=[]
    for i, tick in enumerate(starts):
        ev.extend([Event(tick, 0x90, bytes((60+i, 90)), order=2*i),
                   Event(tick+83, 0x80, bytes((60+i, 0)), order=2*i+1)])
    return Song(0, 480, [Track(ev)])

def test_quantize_length_and_onsets():
    s=make_song((61,))
    assert transform(s,0,length=True)==1
    assert [e.tick for e in s.tracks[0].events]==[120,240]

def test_swing_offbeat_only():
    s=make_song((0,120))
    transform(s,0,swing=50)
    assert s.tracks[0].events[0].tick==0
    assert s.tracks[0].events[2].tick==150

def test_selection_preserves_unselected():
    s=make_song()
    transform(s,0,pairs=[(0,1)],length=True)
    assert s.tracks[0].events[2].tick==181

def test_humanize_reproducible():
    a,b=make_song(),make_song()
    transform(a,0,timing_jitter=8,velocity_jitter=9,seed=123)
    transform(b,0,timing_jitter=8,velocity_jitter=9,seed=123)
    assert [(e.tick,e.data) for e in a.tracks[0].events]==[(e.tick,e.data) for e in b.tracks[0].events]

def test_invalid_atomic():
    s=make_song()
    original=[(e.tick,e.data) for e in s.tracks[0].events]
    with pytest.raises(MidiError): transform(s,0,pairs=[(0,1),(999,1000)])
    assert [(e.tick,e.data) for e in s.tracks[0].events]==original
    assert not s.dirty

def test_invalid_parameter_atomic():
    s=make_song()
    with pytest.raises(MidiError): transform(s,0,swing=101)
    assert not s.dirty

def test_strength_zero_no_change():
    s=make_song()
    assert transform(s,0,strength=0)==0
    assert not s.dirty

def test_midi_roundtrip():
    s=make_song()
    transform(s,0,length=True,swing=25)
    parsed=Song.from_bytes(s.to_bytes())
    assert len(parsed.tracks[0].events)>=4
