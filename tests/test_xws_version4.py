import pytest
from midi import MidiError
from xws_import import import_xws_bytes
from xws_version4 import inspect_xws4


def chunk(tag, body):
    return tag + len(body).to_bytes(4, 'big') + body


def sample(channel=0):
    header = bytearray(64)
    header[8:10] = (480).to_bytes(2, 'big')
    meta = bytearray(33)
    meta[0], meta[2] = 1, channel
    return chunk(b'S4WH', header) + chunk(b'S4WB', b'') + chunk(b'S4WT', meta)


def trailer():
    return b''.join(chunk(tag, bytes(4)) for tag in (b'SCRS', b'SCRA', b'SCRD'))


def test_v4_trailer_import_unchanged():
    assert import_xws_bytes(sample()).to_bytes() == import_xws_bytes(sample() + trailer()).to_bytes()


def test_v4_trailer_detection():
    assert inspect_xws4(sample())['trailer_bytes'] == 0
    assert inspect_xws4(sample() + trailer())['trailer_bytes'] == 36


def test_channel_observation_only():
    assert inspect_xws4(sample(4))['s4wt_channel_observations'][0]['channel_candidate'] == 5
    assert inspect_xws4(sample(16))['s4wt_channel_observations'][0]['channel_candidate'] is None


def test_partial_trailer_rejected():
    with pytest.raises(MidiError, match='Incomplete'):
        import_xws_bytes(sample() + chunk(b'SCRS', bytes(4)))


def test_invalid_trailer_rejected():
    with pytest.raises(MidiError, match='Invalid'):
        import_xws_bytes(sample() + chunk(b'SCRS', b'bad!') + trailer()[12:])


def test_nonfinal_trailer_rejected():
    with pytest.raises(MidiError, match='final'):
        import_xws_bytes(sample() + trailer() + chunk(b'S4ST', b''))
