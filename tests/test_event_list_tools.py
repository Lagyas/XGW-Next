import pytest
from midi import Event
from event_list_tools import matches_event, rewrite_xg_parameter
from event_descriptions import sysex_description
from xg_sysex import parameter_change, decode_parameter_change, smf_sysex_to_wire


def test_filter_search_description():
    assert matches_event(Event(10, 0xb0, bytes([64, 127])), 'Control changes', 'sustain')
    assert not matches_event(Event(10, 0xb0, bytes([64, 127])), 'Notes', 'sustain')


def test_filter_search_raw_hex():
    assert matches_event(Event(10, 0xb0, bytes([91, 80])), query='5b 50')


def test_unknown_category():
    with pytest.raises(ValueError):
        matches_event(Event(0, 0xb0, b'\x07\x40'), 'bogus')


def test_rewrite_preserves_device_and_address():
    event = Event(0, 0xf0, parameter_change((8, 0, 11), b'\x40', 3)[1:])
    result = decode_parameter_change(smf_sysex_to_wire(0xf0, rewrite_xg_parameter(event, values=b'\x64')))
    assert result == {'device': 3, 'address': (8, 0, 11), 'data': b'\x64'}


def test_rewrite_rejects_non_xg():
    with pytest.raises(ValueError):
        rewrite_xg_parameter(Event(0, 0xf0, b'\x41\x10\xf7'))


def test_rewrite_rejects_invalid_bytes():
    event = Event(0, 0xf0, parameter_change((8, 0, 11), b'\x40')[1:])
    with pytest.raises(Exception):
        rewrite_xg_parameter(event, values=b'\xff')


def test_effect_type_uses_catalog():
    text = sysex_description(0xf0, parameter_change((2, 1, 0), bytes([1, 0]))[1:])
    assert 'Reverb Type' in text and 'Hall 1' in text


def test_eq_parameter_label():
    assert 'Multi EQ parameter' in sysex_description(0xf0, parameter_change((2, 0x40, 3), b'\x40')[1:])


def test_drum_setup_label():
    assert 'Drum Setup' in sysex_description(0xf0, parameter_change((0x30, 60, 4), b'\x40')[1:])
