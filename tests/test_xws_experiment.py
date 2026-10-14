import struct
import pytest
from xws_experiment import controlled_s4wt_experiment, format_controlled_experiment


def chunk(tag, payload):
    return tag + struct.pack('>I', len(payload)) + payload


def sample(value, second=0):
    def record(n):
        data = bytearray(37)
        data[7] = n
        data[32:] = b'\4Bass'
        return chunk(b'S4WT', data)
    return chunk(b'S4WH', bytes(64)) + chunk(b'S4WB', b'') * 2 + record(value) + record(second)


def test_single_edit_reports_candidate_not_decoder():
    result = controlled_s4wt_experiment(sample(20), sample(30), track=1,
                                        parameter='volume', before_value=20, after_value=30)
    assert result['candidate_offsets'] == [(7, 20, 30)]
    assert result['controlled_candidate'] and result['verified_decoder'] is False


def test_unrelated_track_change_is_flagged():
    result = controlled_s4wt_experiment(sample(20), sample(30, 5), track=1,
                                        parameter='volume', before_value=20, after_value=30)
    assert result['other_changed_tracks'] == [2]
    assert not result['controlled_candidate']


def test_no_change_not_candidate():
    result = controlled_s4wt_experiment(sample(20), sample(20), track=1,
                                        parameter='volume', before_value=20, after_value=30)
    assert not result['controlled_candidate']


@pytest.mark.parametrize('args', [dict(track=0, parameter='volume', before_value=1, after_value=2),
                                  dict(track=1, parameter='', before_value=1, after_value=2),
                                  dict(track=1, parameter='pan', before_value=2, after_value=2),
                                  dict(track=1, parameter='pan', before_value=-1, after_value=2)])
def test_bad_experiment_declaration(args):
    with pytest.raises(ValueError):
        controlled_s4wt_experiment(sample(20), sample(30), **args)


def test_report_explicitly_unverified():
    report = format_controlled_experiment(sample(20), sample(30), track=1,
                                          parameter='volume', before_value=20, after_value=30)
    assert 'NOT confirmed' in report
