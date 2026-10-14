import pytest
from midi import MidiError, Song, Track
from multiport_state import effective_port_channels, save_routing, load_routing, sidecar_path

def test_independent_masks():
    assert ('A', 0) not in effective_port_channels('A', {0}, set())
    assert ('B', 0) in effective_port_channels('B', set(), set())

def test_solo_mask():
    assert effective_port_channels('A', set(), {3}) == {('A', 3)}

def test_invalid_channel():
    with pytest.raises(MidiError): effective_port_channels('A', {16}, set())

def test_roundtrip(tmp_path):
    song = Song(1, 480, [Track([])])
    path = tmp_path / 'song.mid'
    save_routing(path, song, {0: ('B', 3)}, 'A')
    assert load_routing(path, song, 'A') == {0: ('B', 3)}

def test_missing_sidecar(tmp_path):
    assert load_routing(tmp_path / 'absent.mid', Song(1, 480, [Track([])]), 'A') == {}

def test_corrupt_sidecar(tmp_path):
    path = tmp_path / 'bad.mid'
    sidecar_path(path).write_text('{bad')
    with pytest.raises(MidiError): load_routing(path, Song(1, 480, [Track([])]), 'A')
