import struct
import pytest
from midi import MidiError
from xws_import import inspect_s4wt_records, format_s4wt_report


def chunk(tag, data):
    return tag + struct.pack('>I', len(data)) + data


def sample():
    header = bytearray(64)
    header[8:10] = (480).to_bytes(2, 'big')
    named = bytearray(37)
    named[0] = 1
    named[32] = 4
    named[33:37] = b'Bass'
    unnamed = bytearray(33)
    unnamed[0] = 1
    return (chunk(b'S4WH', header) + chunk(b'S4WB', b'') * 2 +
            chunk(b'S4WT', named) + chunk(b'S4WT', unnamed) +
            chunk(b'S4WT', bytes(33)))


def test_alignment_preserves_unnamed_and_excludes_extra():
    rows = inspect_s4wt_records(sample())
    assert [r['sequence_track'] for r in rows] == [1, 2, None]
    assert [r['name'] for r in rows] == ['Bass', None, None]


def test_report_does_not_infer_mixer():
    report = format_s4wt_report(sample())
    assert 'Bass' in report and 'Additional S4WT records' in report
    assert 'No volume, pan, bank or channel is inferred' in report


def test_short_s4wt_rejected():
    with pytest.raises(MidiError, match='Truncated S4WT'):
        inspect_s4wt_records(chunk(b'S4WH', bytes(64)) + chunk(b'S4WT', bytes(32)))


def test_real_sample_s4wt_alignment():
    from pathlib import Path
    p = Path('/mnt/data/A Dream of a Dream.XWS')
    if not p.exists():
        pytest.skip('Reference XWS not available')
    rows = inspect_s4wt_records(p.read_bytes())
    assert len([r for r in rows if r['sequence_track'] is not None]) == 24
    assert next(r for r in rows if r['sequence_track'] == 3)['name'] == 'Bass'
    assert len(rows) > 24
