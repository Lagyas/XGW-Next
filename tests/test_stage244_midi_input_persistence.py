import sys
import tempfile
import zipfile
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from project_bundle import save_project, load_project_midi_inputs, validate_midi_inputs
from project_recovery import write_recovery, recovery_path, snapshot_fingerprint


def song():
    return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64')]), Track([])])


def test_input_ports_roundtrip():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'a.xgwn'
        save_project(path, song(), midi_inputs={0: 'Yamaha USB MIDI 1', 1: 'Roland IN B'})
        assert load_project_midi_inputs(path, 2) == {0: 'Yamaha USB MIDI 1', 1: 'Roland IN B'}


def test_legacy_project_has_no_inputs():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'a.xgwn'
        save_project(path, song())
        assert load_project_midi_inputs(path, 2) == {}


@pytest.mark.parametrize('routes', [{-1: 'In'}, {2: 'In'}, {0: ''}, {0: ' '}, {0: 42}, {'0': 'In'}])
def test_reject_invalid_input_routes(routes):
    with pytest.raises(MidiError):
        validate_midi_inputs(routes, 2)


def test_reject_corrupt_project_input_data():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'a.xgwn'
        save_project(path, song())
        with zipfile.ZipFile(path, 'a') as archive:
            archive.writestr('midi-inputs.json', '{"99": "Missing track"}')
        with pytest.raises(MidiError):
            load_project_midi_inputs(path, 2)


def test_recovery_keeps_inputs():
    with tempfile.TemporaryDirectory() as directory:
        write_recovery('example.mid', song(), directory=directory, midi_inputs={1: 'Input B'})
        assert load_project_midi_inputs(recovery_path('example.mid', directory), 2) == {1: 'Input B'}


def test_autosave_fingerprint_tracks_input_changes():
    a = snapshot_fingerprint(song(), midi_inputs={0: 'A'})
    b = snapshot_fingerprint(song(), midi_inputs={0: 'B'})
    assert a != b
