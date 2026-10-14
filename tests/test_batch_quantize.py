import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
import pytest
from midi import Song, Track, Event, MidiError
from batch_quantize import transform_tracks


def song():
    return Song(1, 480, [Track([Event(61,0x90,bytes((60,90))), Event(144,0x80,bytes((60,0)))]),
                         Track([Event(181,0x90,bytes((64,85))), Event(264,0x80,bytes((64,0)))]),
                         Track([Event(20,0x90,bytes((67,70))), Event(103,0x80,bytes((67,0)))])])


def test_batch_selected_tracks_only():
    s=song()
    assert transform_tracks(s,[0,2],length=True)==2
    assert s.tracks[0].events[0].tick==120
    assert s.tracks[1].events[0].tick==181
    assert s.tracks[2].events[0].tick==0


def test_duplicate_indices_are_not_double_processed():
    s=song()
    assert transform_tracks(s,[0,0],swing=50)==1


def test_invalid_index_atomic():
    s=song(); before=s.to_bytes()
    with pytest.raises(MidiError): transform_tracks(s,[0,99])
    assert s.to_bytes()==before and not s.dirty


def test_invalid_options_atomic():
    s=song(); before=s.to_bytes()
    with pytest.raises(MidiError): transform_tracks(s,[0,1],velocity_jitter=200)
    assert s.to_bytes()==before and not s.dirty


def test_empty_selection_rejected():
    with pytest.raises(MidiError): transform_tracks(song(),[])


def test_humanize_deterministic():
    a,b=song(),song()
    transform_tracks(a,[0,1],timing_jitter=8,velocity_jitter=4,seed=42)
    transform_tracks(b,[0,1],timing_jitter=8,velocity_jitter=4,seed=42)
    assert a.to_bytes()==b.to_bytes()


def test_noop_does_not_mark_dirty():
    s=song()
    assert transform_tracks(s,[0,1],strength=0)==0
    assert not s.dirty
