from event_descriptions import sysex_description
from xg_sysex import parameter_change


def desc(addr, value):
    return sysex_description(0xf0, parameter_change(addr, bytes([value]))[1:])


def test_program_uses_one_based_display():
    assert 'Program Number = 1 (MIDI 00)' in desc((8, 0, 3), 0)


def test_receive_channel_display():
    assert 'channel 16' in desc((8, 15, 4), 15)
    assert 'Off' in desc((8, 0, 4), 127)


def test_note_shift_is_signed():
    assert '+0 semitones' in desc((8, 0, 8), 64)
    assert '-12 semitones' in desc((8, 0, 8), 52)


def test_mono_poly_and_pan():
    assert 'Mono' in desc((8, 0, 5), 0)
    assert 'Poly' in desc((8, 0, 5), 1)
    assert 'center 64' in desc((8, 0, 14), 64)


def test_unknown_part_parameter_keeps_hex():
    assert 'Parameter 7D = 0A' in desc((8, 0, 0x7d), 10) or 'Parameter 7D = 10' in desc((8, 0, 0x7d), 10)


def test_multibyte_value_keeps_raw_hex():
    raw = parameter_change((8, 0, 0x09), b'\x01\x02')
    assert '01 02' in sysex_description(0xf0, raw[1:])
