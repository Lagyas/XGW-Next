from event_descriptions import sysex_description


def gs_dt1(address, data, checksum=None):
    cs = (-sum(address) - sum(data)) & 0x7f if checksum is None else checksum
    return bytes([0x41, 0x10, 0x42, 0x12, *address, *data, cs, 0xf7])


def test_gs_reset():
    assert 'GS Reset' in sysex_description(0xf0, gs_dt1((0x40, 0, 0x7f), (0,)))


def test_gs_master_volume():
    assert 'Master Volume = 64' in sysex_description(0xf0, gs_dt1((0x40, 0, 4), (0x64,)))


def test_gs_part_volume():
    assert 'Part 1 Volume' in sysex_description(0xf0, gs_dt1((0x40, 0x10, 0x15), (0x64,)))


def test_gs_bad_checksum_is_not_silently_accepted():
    assert 'bad checksum' in sysex_description(0xf0, gs_dt1((0x40, 0, 4), (0x64,), 0))


def test_gs_unknown_address_is_hex():
    assert 'address 40 00 77' in sysex_description(0xf0, gs_dt1((0x40, 0, 0x77), (0x01,)))


def test_gm_system_on():
    assert 'GM System On' in sysex_description(0xf0, bytes([0x7e, 0x7f, 9, 1, 0xf7]))


def test_gm2_system_on():
    assert 'GM2 System On' in sysex_description(0xf0, bytes([0x7e, 0x7f, 9, 3, 0xf7]))


def test_unknown_roland_keeps_hex():
    assert 'Roland SysEx' in sysex_description(0xf0, bytes([0x41, 0x10, 0x42, 0xf7]))
