import struct
from xws_import import import_xws_bytes
from midi import Song


def chunk(kind, data):
    return kind + struct.pack('>I', len(data)) + data


def sample(track, metadata=b''):
    header = bytearray(64)
    header[8:10] = (480).to_bytes(2, 'big')
    return chunk(b'S4WH', header) + chunk(b'S4WB', track) + metadata


def test_s4wt_name_becomes_track_name():
    name = b'Bass Guitar'
    metadata = bytes(32) + bytes((len(name),)) + name + b'\x00'
    metadata = b'\x01' + metadata[1:]
    song = import_xws_bytes(sample(b'', chunk(b'S4WT', metadata)))
    assert song.tracks[0].name() == 'Bass Guitar'
    assert Song.from_bytes(song.to_bytes()).tracks[0].name() == 'Bass Guitar'


def test_malformed_s4wt_name_ignored():
    metadata = b'\x01' + bytes(31) + b'\x7f' + b'\x01'
    song = import_xws_bytes(sample(b'', chunk(b'S4WT', metadata)))
    assert song.tracks[0].name() == 'Untitled'


def test_note_off_precedes_retrigger_at_same_tick():
    # First note C4 0..10, second note C4 10..15.
    data = bytes.fromhex('00 90 3c 64 00 00 00 0a 0a 90 3c 50 00 00 00 05')
    events = import_xws_bytes(sample(data)).tracks[0].events
    assert [(e.tick, e.status & 0xf0) for e in events] == [
        (0, 0x90), (10, 0x80), (10, 0x90), (15, 0x80)]


def test_zero_duration_note_on_before_off():
    data = bytes.fromhex('00 90 3c 64 00 00 00 00')
    events = import_xws_bytes(sample(data)).tracks[0].events
    assert [e.status & 0xf0 for e in events] == [0x90, 0x80]
