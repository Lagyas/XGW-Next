import pytest
from midi import MidiError
from xg_mixer_bridge import (default_part_assignments, encode_part_assignments,
                             decode_part_assignments)


def test_mapping_roundtrip():
    mapping = default_part_assignments()
    mapping[1] = (16, 15)
    assert decode_part_assignments(encode_part_assignments(mapping)) == mapping


def test_mapping_json_roundtrip():
    import json
    mapping = default_part_assignments()
    assert decode_part_assignments(json.loads(json.dumps(encode_part_assignments(mapping)))) == mapping


@pytest.mark.parametrize('payload', [None, {}, {'1': [1, 0]}, [],
                                     {str(i): [i, 0] for i in range(1, 17)} | {'17': [1, 0]}])
def test_mapping_rejects_invalid_payload(payload):
    with pytest.raises(MidiError):
        decode_part_assignments(payload)


def test_mapping_rejects_invalid_device():
    mapping = encode_part_assignments(default_part_assignments())
    mapping['5'] = [5, 16]
    with pytest.raises(MidiError):
        decode_part_assignments(mapping)
