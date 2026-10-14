import pytest
from safe_save import atomic_write


def test_new_file(tmp_path):
    p = tmp_path / 'song.mid'
    atomic_write(p, b'MIDI')
    assert p.read_bytes() == b'MIDI'
    assert not (tmp_path / 'song.mid.bak').exists()


def test_overwrite_retains_backup(tmp_path):
    p = tmp_path / 'song.mid'
    p.write_bytes(b'old')
    atomic_write(p, b'new')
    assert p.read_bytes() == b'new'
    assert (tmp_path / 'song.mid.bak').read_bytes() == b'old'


def test_bad_payload_preserves_file(tmp_path):
    p = tmp_path / 'song.mid'
    p.write_bytes(b'original')
    with pytest.raises(TypeError):
        atomic_write(p, 'not bytes')
    assert p.read_bytes() == b'original'


def test_no_backup_option(tmp_path):
    p = tmp_path / 'song.mid'
    p.write_bytes(b'old')
    atomic_write(p, b'new', backup=False)
    assert p.read_bytes() == b'new'
    assert not (tmp_path / 'song.mid.bak').exists()
