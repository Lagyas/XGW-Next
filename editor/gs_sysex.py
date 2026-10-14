"""Conservative Roland GS DT1 and universal GM SysEx descriptions.

Only validated complete messages are interpreted. Unknown addresses remain hex.
"""

GS_PARAMETERS = {
    (0x40, 0x00, 0x7f): 'GS Reset',
    (0x40, 0x00, 0x04): 'Master Volume',
    (0x40, 0x00, 0x05): 'Master Key Shift',
    (0x40, 0x01, 0x30): 'Reverb Macro',
    (0x40, 0x01, 0x38): 'Chorus Macro',
}


def describe_roland(raw):
    """Return a GS DT1 description or None for other/invalid Roland messages."""
    if (len(raw) < 11 or raw[0] != 0xf0 or raw[-1] != 0xf7
            or raw[1] != 0x41 or raw[3] != 0x42 or raw[4] != 0x12
            or any(byte > 127 for byte in raw[1:-1])):
        return None
    address = tuple(raw[5:8])
    data = raw[8:-2]
    if not data:
        return None
    checksum = raw[-2]
    expected = (-sum(address) - sum(data)) & 0x7f
    if checksum != expected:
        return f'Roland GS DT1 (bad checksum: {checksum:02X}, expected {expected:02X}): ' + raw.hex(' ').upper()
    name = GS_PARAMETERS.get(address)
    if name is None and address[0] == 0x40 and 0x10 <= address[1] <= 0x1f:
        part = (address[1] & 0x0f) + 1
        part_names = {0x02: 'Receive Channel', 0x15: 'Volume', 0x16: 'Pan',
                      0x19: 'Reverb Send', 0x1a: 'Chorus Send'}
        name = f'Part {part} {part_names.get(address[2], "Parameter " + format(address[2], "02X"))}'
    if name is None:
        name = 'address ' + ' '.join(f'{v:02X}' for v in address)
    return f'Roland GS (device {raw[2] + 1}): {name} = {data.hex(" ").upper()}'


def describe_universal(raw):
    """Recognize complete Universal Non-Realtime GM messages."""
    if (len(raw) != 6 or raw[0] != 0xf0 or raw[-1] != 0xf7
            or raw[1] != 0x7e or raw[3] != 0x09):
        return None
    name = {0x01: 'GM System On', 0x02: 'GM System Off', 0x03: 'GM2 System On'}.get(raw[4])
    if name is None:
        return None
    device = 'all devices' if raw[2] == 0x7f else f'device {raw[2] + 1}'
    return f'Universal MIDI: {name} ({device})'
