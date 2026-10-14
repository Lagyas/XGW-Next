from midi import Event
from event_descriptions import describe_event, sysex_description
from xg_sysex import parameter_change


def test_controller_name():
    assert 'Reverb Send' in describe_event(Event(0, 0xb0, bytes([91, 80])))


def test_program_is_one_based():
    assert 'Program Change: 1' in describe_event(Event(0, 0xc0, b'\x00'))


def test_pitch_bend_center():
    assert '+0' in describe_event(Event(0, 0xe0, bytes([0, 64])))


def test_xg_system_on():
    raw = parameter_change((0, 0, 0x7e), b'\x00')
    assert 'XG System On' in sysex_description(0xf0, raw[1:])


def test_xg_part_volume():
    raw = parameter_change((8, 0, 0x0b), b'\x64')
    assert 'Part 1 Volume' in sysex_description(0xf0, raw[1:])


def test_unknown_xg_retains_address():
    raw = parameter_change((0x30, 0x22, 0x11), b'\x10')
    assert '30 22 11' in sysex_description(0xf0, raw[1:])


def test_roland_is_not_misidentified():
    assert 'Roland SysEx' in sysex_description(0xf0, bytes([0x41, 0x10, 0x42, 0xf7]))


def test_f7_not_decoded_as_new_message():
    assert 'continuation' in sysex_description(0xf7, b'\x43\x10\x4c\xf7')


def test_incomplete_sysex_safe():
    assert 'Incomplete' in sysex_description(0xf0, b'\x43\x10')
