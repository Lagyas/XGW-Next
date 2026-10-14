import struct
import pytest
from midi import MidiError
from xws_import import compare_s4wt_records, format_s4wt_comparison


def chunk(kind, body):
    return kind + struct.pack('>I', len(body)) + body


def sample(prefix=0, name=b'Bass', tracks=1):
    header = bytearray(64)
    header[8:10] = (480).to_bytes(2, 'big')
    record = bytearray(33 + len(name))
    record[0] = 1
    record[7] = prefix
    record[32] = len(name)
    record[33:] = name
    return chunk(b'S4WH', header) + chunk(b'S4WB', b'') * tracks + chunk(b'S4WT', record) * tracks


def test_identical_has_no_differences():
    assert compare_s4wt_records(sample(), sample()) == []


def test_byte_difference_reports_offset_not_guessed_meaning():
    rows = compare_s4wt_records(sample(12), sample(24))
    assert rows[0]['fixed_prefix_changes'] == [(7, 12, 24)]
    report = format_s4wt_comparison(sample(12), sample(24))
    assert 'Fixed offset 07: 0C -> 18' in report
    assert 'No channel, volume, pan or bank is inferred' in report


def test_name_change_is_separate_from_fixed_prefix():
    row = compare_s4wt_records(sample(name=b'Bass'), sample(name=b'Synth'))[0]
    assert row['fixed_prefix_changes'] == []
    assert row['name_before'] == b'Bass'
    assert row['name_after'] == b'Synth'
    assert row['variable_tail_changed']


def test_track_count_mismatch_rejected():
    with pytest.raises(MidiError, match='different MIDI track counts'):
        compare_s4wt_records(sample(tracks=1), sample(tracks=2))


def test_truncated_metadata_rejected():
    broken = chunk(b'S4WH', bytes(64)) + chunk(b'S4WB', b'') + chunk(b'S4WT', b'123')
    with pytest.raises(MidiError, match='Truncated S4WT'):
        compare_s4wt_records(sample(), broken)
