import struct
import pytest
from xws_experiment import corroborate_s4wt_experiments
from midi import Song, Track, Event
from project_recovery import write_recovery, recovery_path
from project_bundle import load_project_track_properties


def chunk(tag, data):
    return tag + struct.pack('>I', len(data)) + data


def sample(value, second=0, offset=7):
    rows = []
    for n in (value, second):
        body = bytearray(37)
        body[offset] = n
        body[32:] = b'\4Bass'
        rows.append(chunk(b'S4WT', body))
    return chunk(b'S4WH', bytes(64)) + chunk(b'S4WB', b'') * 2 + b''.join(rows)


def experiment(a, b, **kwargs):
    return (sample(a, **kwargs), sample(b, **kwargs), 1, 'volume', a, b)


def test_two_distinct_edits_stable_offset_is_only_evidence():
    result = corroborate_s4wt_experiments([experiment(20, 30), experiment(30, 50)])
    assert result['stable_candidate_offsets'] == [7]
    assert result['all_isolated']
    assert result['verified_decoder'] is False


def test_other_track_change_disqualifies_evidence():
    contaminated = (sample(30), sample(50, second=10), 1, 'volume', 30, 50)
    result = corroborate_s4wt_experiments([experiment(20, 30), contaminated])
    assert result['stable_candidate_offsets'] == []


def test_changed_offsets_do_not_agree():
    result = corroborate_s4wt_experiments([experiment(20, 30), experiment(30, 50, offset=8)])
    assert result['stable_candidate_offsets'] == []


@pytest.mark.parametrize('data', [[], [experiment(20,30)],
    [experiment(20,30), experiment(20,30)],
    [experiment(20,30), (sample(30),sample(50),2,'volume',30,50)],
    [experiment(20,30), (sample(30),sample(50),1,'pan',30,50)]])
def test_bad_comparison_sets(data):
    with pytest.raises(ValueError):
        corroborate_s4wt_experiments(data)


def test_recovery_preserves_source_channel_observations(tmp_path):
    song = Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64')])])
    props = {'source': 'XGworks S4WT', 'tracks': [
        {'track': 1, 'channel': 3, 'verified': True}]}
    source = tmp_path / 'song.xgwn'
    write_recovery(source, song, directory=tmp_path / 'recovery',
                   xws_track_properties=props)
    assert load_project_track_properties(recovery_path(source, tmp_path / 'recovery'), 1) == props
