import pytest
from midi import MidiError
from xg_mixer_bridge import default_part_assignments, normalize_part_assignments


def test_default_mapping():
    mapping = default_part_assignments(3)
    assert len(mapping) == 16
    assert mapping[1] == (1, 3)
    assert mapping[16] == (16, 3)


def test_custom_mapping_preserved():
    mapping = default_part_assignments()
    mapping[1] = (12, 4)
    mapping[16] = [2, 15]
    result = normalize_part_assignments(mapping)
    assert result[1] == (12, 4)
    assert result[16] == (2, 15)
    assert result is not mapping


def test_incomplete_mapping_rejected():
    with pytest.raises(MidiError):
        normalize_part_assignments({1: (1, 0)})


def test_invalid_mapping_rejected():
    mapping = default_part_assignments()
    for bad in ((0, 0), (17, 0), (1, 16), (True, 0), (1, -1)):
        mapping[2] = bad
        with pytest.raises(MidiError):
            normalize_part_assignments(mapping)


def test_invalid_default_device_rejected():
    with pytest.raises(MidiError):
        default_part_assignments(16)
