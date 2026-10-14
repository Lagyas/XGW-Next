from xws_track_channel import track_channel_rows, format_track_channel_report
from xws_import import import_xws_bytes


def chunk(tag, body):
    return tag + len(body).to_bytes(4, 'big') + body


def sample(value):
    header = bytearray(64)
    header[8:10] = (480).to_bytes(2, 'big')
    metadata = bytearray(33)
    metadata[0], metadata[2] = 1, value
    return chunk(b'S4WH', header) + chunk(b'S4WB', b'') + chunk(b'S4WT', metadata)


def test_channel_1():
    assert track_channel_rows(sample(0)) == ((1, 1),)


def test_channel_5():
    assert track_channel_rows(sample(4)) == ((1, 5),)


def test_unsupported_channel_not_guessed():
    assert track_channel_rows(sample(16)) == ((1, None),)


def test_report_contains_provenance():
    report = format_track_channel_report(sample(4))
    assert 'read-only' in report and 'MIDI channel 5' in report


def test_inspection_does_not_mutate_midi():
    raw = sample(4)
    before = import_xws_bytes(raw).to_bytes()
    track_channel_rows(raw)
    assert import_xws_bytes(raw).to_bytes() == before
