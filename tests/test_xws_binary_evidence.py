import struct
import pytest
from midi import MidiError
from xws_experiment import compare_xws_binary_evidence


def chunk(tag, body):
    return tag + struct.pack('>I', len(body)) + body


def sample(cc=110, padding=b''):
    track = b'\x00\xb0\x07' + bytes([cc])
    return chunk(b'S4WH', bytes(64)) + chunk(b'S4WB', track) + chunk(b'S4WT', bytes(33)) + chunk(b'S4ST', padding)


def test_cc7_change_detected_without_claiming_s4wt():
    result = compare_xws_binary_evidence(sample(), sample(80))
    assert result['s4wt_changes'] == []
    assert result['changed_chunks'][0]['kind'] == 'S4WB'
    assert result['changed_chunks'][0]['cc_before'] == [(0, 0, 7, 110)]
    assert result['changed_chunks'][0]['cc_after'] == [(0, 0, 7, 80)]


def test_length_change_tracks_edit_span():
    result = compare_xws_binary_evidence(sample(), sample(padding=b'abc'))
    assert result['after_length'] - result['before_length'] == 3
    assert result['changed_chunks'][0]['kind'] == 'S4ST'


def test_identical_files():
    result = compare_xws_binary_evidence(sample(), sample())
    assert result['changed_chunks'] == []
    assert result['s4wt_changes'] == []


def test_reports_added_trailing_chunk():
    result = compare_xws_binary_evidence(sample(), sample() + chunk(b'ABCD', b''))
    assert result['changed_chunks'][-1]['added'] is True


def test_rejects_wrong_type():
    with pytest.raises(TypeError):
        compare_xws_binary_evidence('bad', b'')
