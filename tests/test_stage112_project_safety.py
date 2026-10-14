import sys
from pathlib import Path
import zipfile
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from midi import Song, Track, Event, MidiError
from project_bundle import save_project, load_project

def song(pitch=60):
    return Song(1, 480, [Track([Event(0, 0x90, bytes([pitch, 90]))])])

def test_overwrite_creates_valid_previous_project_backup(tmp_path):
    path = tmp_path / "demo.xgwn"
    save_project(path, song(60))
    original = path.read_bytes()
    save_project(path, song(64))
    backup = path.with_name(path.name + ".bak")
    assert backup.read_bytes() == original
    assert load_project(backup)[0].tracks[0].events[0].data[0] == 60
    assert load_project(path)[0].tracks[0].events[0].data[0] == 64

def test_invalid_save_preserves_existing_project_and_backup(tmp_path):
    path = tmp_path / "demo.xgwn"
    save_project(path, song())
    original = path.read_bytes()
    with pytest.raises(MidiError):
        save_project(path, song(64), routes={0: ("Port", 17)})
    assert path.read_bytes() == original
    assert not path.with_name(path.name + ".bak").exists()

def test_first_save_has_no_backup(tmp_path):
    path = tmp_path / "demo.xgwn"
    save_project(path, song())
    assert zipfile.is_zipfile(path)
    assert not path.with_name(path.name + ".bak").exists()
