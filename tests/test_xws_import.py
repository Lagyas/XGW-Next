import struct
import pytest
from midi import MidiError, Song
from xws_import import import_xws_bytes, import_xws
from pathlib import Path


def chunk(kind, data):
    return kind + struct.pack('>I', len(data)) + data


def fixture(body):
    header = bytearray(64)
    header[8:10] = (480).to_bytes(2, 'big')
    return chunk(b'S4WH', header) + chunk(b'S4WB', body)


def test_note_duration_creates_off_and_roundtrips():
    raw = fixture(bytes.fromhex('00 90 3c 64 00 00 01 e0 81 70 b0 07 64'))
    song = import_xws_bytes(raw)
    assert song.division == 480
    assert [(e.tick, e.status) for e in song.tracks[0].events] == [(0, 0x90), (240, 0xb0), (480, 0x80)]
    assert len(Song.from_bytes(song.to_bytes()).tracks[0].events) == 3


def test_running_status_and_zero_duration():
    song = import_xws_bytes(fixture(bytes.fromhex('00 91 3c 64 00 00 00 00 00 3e 60 00 00 00 05')))
    assert [(e.tick, e.status) for e in song.tracks[0].events] == [(0, 0x91), (0, 0x81), (0, 0x91), (5, 0x81)]


def test_truncated_duration_rejected():
    with pytest.raises(MidiError, match='duration'):
        import_xws_bytes(fixture(bytes.fromhex('00 90 3c 64 00 00')))


def test_corrupt_chunk_rejected():
    with pytest.raises(MidiError):
        import_xws_bytes(fixture(b'')[:-1])


def test_unknown_chunk_rejected():
    with pytest.raises(MidiError, match='Unknown'):
        import_xws_bytes(fixture(b'') + chunk(b'BAD!', b''))


def test_real_xws_sample():
    path = Path('/mnt/data/A Dream of a Dream.XWS')
    if not path.exists():
        pytest.skip('External reference project not supplied')
    original = path.read_bytes()
    song = import_xws(path)
    assert len(song.tracks) == 24
    assert song.division == 480
    assert sum(len(t.events) for t in song.tracks) == 10941
    assert Song.from_bytes(song.to_bytes()).division == 480
    assert path.read_bytes() == original
