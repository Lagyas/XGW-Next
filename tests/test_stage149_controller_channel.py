import pytest
from midi import MidiError
from piano_roll import controller_channel


def test_auto_uses_first_note_channel():
    assert controller_channel(None, [(0, 100, 60, 12, 90, 0, 1)]) == 12


def test_auto_defaults_to_channel_one():
    assert controller_channel(None, []) == 1


@pytest.mark.parametrize('channel', ['1', '9', '16'])
def test_explicit_channel(channel):
    assert controller_channel(None, [], channel) == int(channel)


@pytest.mark.parametrize('channel', ['0', '17', 'bad', None])
def test_invalid_channel(channel):
    with pytest.raises(MidiError):
        controller_channel(None, [], channel)
