"""XGworks S4WT records are positional, including unnamed tracks."""
import struct
from pathlib import Path
from xws_import import import_xws_bytes


def chunk(kind, body):
    return kind + struct.pack('>I', len(body)) + body


def test_unnamed_s4wt_does_not_shift_subsequent_names():
    header = bytearray(64)
    header[8:10] = (480).to_bytes(2, 'big')
    def label(name):
        body = bytearray(33)
        body[0] = 1
        body[32] = len(name)
        return bytes(body) + name
    raw = (chunk(b'S4WH', header) + chunk(b'S4WB', b'') * 3
           + chunk(b'S4WT', label(b'')) + chunk(b'S4WT', label(b'Bass'))
           + chunk(b'S4WT', label(b'Synth')))
    song = import_xws_bytes(raw)
    assert [track.name() for track in song.tracks] == ['Untitled', 'Bass', 'Synth']


def test_later_metadata_groups_do_not_supply_missing_track_names():
    header = bytearray(64)
    header[8:10] = (480).to_bytes(2, 'big')
    raw = chunk(b'S4WH', header) + chunk(b'S4WB', b'')
    raw += chunk(b'S4WT', b'\0' * 33)
    raw += chunk(b'S4WT', b'\1' + b'\0' * 31 + b'\4Late')
    assert import_xws_bytes(raw).tracks[0].name() == 'Untitled'


def test_real_xws_first_track_is_not_misnamed():
    path = Path('/mnt/data/A Dream of a Dream.XWS')
    if not path.exists():
        return
    from xws_import import import_xws
    song = import_xws(path)
    assert song.tracks[0].name() == 'A Dream of a Dream'
    assert song.tracks[1].name() == 'EX'
    assert song.tracks[2].name() == 'Bass'
    assert song.tracks[3].name() == 'Synth'
