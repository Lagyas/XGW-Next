"""Human-readable MIDI and Yamaha XG event descriptions for Event List.

Unknown manufacturer-specific messages are deliberately shown as raw hex.
SMF F7 continuation messages are not decoded as standalone SysEx.
"""
from gs_sysex import describe_roland, describe_universal
from cc_names import cc_label
from xg_sysex import decode_parameter_change, smf_sysex_to_wire
from xg_effect_catalog import effect_type_name

XG_EFFECT_TYPES = {(0x02, 0x01): 'Hall 1', (0x02, 0x02): 'Hall 2',
                   (0x02, 0x03): 'Room 1', (0x02, 0x04): 'Room 2',
                   (0x41, 0x00): 'Chorus 1', (0x42, 0x00): 'Celeste 1'}
XG_SYSTEM = {(0, 0, 0x7e): 'XG System On', (0, 0, 0x7f): 'All Parameter Reset'}
XG_EFFECT_ADDRESSES = {(2, 1, 0): 'Reverb Type', (2, 1, 1): 'Reverb Type LSB',
                       (2, 1, 0x20): 'Chorus Type', (2, 1, 0x21): 'Chorus Type LSB',
                       (2, 1, 0x40): 'Variation Type', (2, 1, 0x41): 'Variation Type LSB'}
XG_PART_PARAMETERS = {0x00: 'Element Reserve', 0x01: 'Bank Select MSB',
                      0x02: 'Bank Select LSB', 0x03: 'Program Number',
                      0x04: 'Receive Channel', 0x05: 'Mono/Poly Mode',
                      0x06: 'Same Note Number Key On Assign', 0x07: 'Part Mode',
                      0x08: 'Note Shift', 0x09: 'Detune', 0x0b: 'Volume',
                      0x0c: 'Velocity Sense Depth', 0x0d: 'Velocity Sense Offset',
                      0x0e: 'Pan', 0x12: 'Chorus Send', 0x13: 'Reverb Send',
                      0x14: 'Variation Send'}


def _xg_part_value(parameter, payload):
    """Add an interpreted value without hiding the exact transmitted bytes."""
    if len(payload) != 1:
        return payload.hex(' ').upper()
    value = payload[0]
    if parameter == 0x03:
        return f'{value + 1} (MIDI {value:02X})'
    if parameter == 0x04:
        return 'Off' if value == 127 else f'channel {value + 1}' if value < 16 else f'{value:02X}'
    if parameter == 0x05:
        return {0: 'Mono', 1: 'Poly'}.get(value, str(value))
    if parameter == 0x08:
        return f'{value - 64:+d} semitones (raw {value:02X})'
    if parameter == 0x0e:
        return f'{value} (center 64)'
    return str(value)


def sysex_description(status, data):
    if status == 0xf7:
        return 'SysEx continuation/escape: ' + bytes(data).hex(' ').upper()[:100]
    raw = smf_sysex_to_wire(status, data)
    if raw is None:
        return 'Incomplete/invalid SysEx: ' + bytes(data).hex(' ').upper()[:100]
    decoded = decode_parameter_change(raw)
    if decoded:
        address = decoded['address']
        payload = decoded['data']
        prefix = f"Yamaha XG (device {decoded['device'] + 1})"
        if address in XG_SYSTEM:
            return f'{prefix}: {XG_SYSTEM[address]} — {payload.hex(" ").upper()}'
        if address[0] == 0x02 and address[1] == 0x01 and address[2] in (0, 0x20, 0x40) and len(payload) >= 2:
            bus = {0: 'reverb', 0x20: 'chorus', 0x40: 'variation'}[address[2]]
            name = effect_type_name(bus, payload[0], payload[1])
            return f'{prefix}: {bus.title()} Type = {name} ({payload.hex(" ").upper()})'
        if address[0] == 0x02 and address[1] == 0x01 and address[2] in range(0x02, 0x10):
            return f'{prefix}: Reverb parameter {address[2] - 1} = {payload.hex(" ").upper()}'
        if address[0] == 0x02 and address[1] == 0x01 and address[2] in range(0x22, 0x30):
            return f'{prefix}: Chorus parameter {address[2] - 0x21} = {payload.hex(" ").upper()}'
        if address[0] == 0x02 and address[1] == 0x01 and address[2] in range(0x42, 0x50):
            return f'{prefix}: Variation parameter {address[2] - 0x41} = {payload.hex(" ").upper()}'
        if address[0] == 0x02 and address[1] == 0x40:
            return f'{prefix}: Multi EQ parameter {address[2]:02X} = {payload.hex(" ").upper()}'
        if address[0] == 0x30 and 0 <= address[1] <= 0x7f:
            return f'{prefix}: Drum Setup parameter {address[2]:02X} (key {address[1]}, address {address[0]:02X} {address[1]:02X} {address[2]:02X}) = {payload.hex(" ").upper()}'
        if address in XG_EFFECT_ADDRESSES:
            label = XG_EFFECT_ADDRESSES[address]
            if len(payload) >= 2 and label.endswith('Type'):
                name = XG_EFFECT_TYPES.get(tuple(payload[:2]))
                if name:
                    return f'{prefix}: {label} = {name} ({payload.hex(" ").upper()})'
            return f'{prefix}: {label} = {payload.hex(" ").upper()}'
        if address[0] == 0x08 and 0 <= address[1] <= 0x0f:
            part = address[1] + 1
            name = XG_PART_PARAMETERS.get(address[2], f'Parameter {address[2]:02X}')
            return f'{prefix}: Part {part} {name} = {_xg_part_value(address[2], payload)}'
        return f'{prefix}: address {address[0]:02X} {address[1]:02X} {address[2]:02X} = {payload.hex(" ").upper()}'
    if len(raw) >= 3 and raw[1] == 0x43:
        return 'Yamaha SysEx (unrecognized model/format): ' + raw.hex(' ').upper()[:100]
    if len(raw) >= 3 and raw[1] == 0x41:
        return describe_roland(raw) or ('Roland SysEx: ' + raw.hex(' ').upper()[:100])
    if len(raw) >= 3 and raw[1] in (0x7e, 0x7f):
        return describe_universal(raw) or ('Universal MIDI SysEx: ' + raw.hex(' ').upper()[:100])
    return 'SysEx: ' + raw.hex(' ').upper()[:100]


def describe_event(event):
    status = event.status
    data = event.data
    if status in (0xf0, 0xf7):
        return sysex_description(status, data)
    if status == 0xff:
        return event.description()
    kind = status & 0xf0
    if kind == 0xb0 and len(data) >= 2:
        return f'{cc_label(data[0])} = {data[1]}'
    if kind == 0xc0 and data:
        return f'Program Change: {data[0] + 1} (MIDI value {data[0]})'
    if kind == 0xe0 and len(data) >= 2:
        value = data[0] | (data[1] << 7)
        return f'Pitch Bend: {value - 8192:+d} (14-bit {value})'
    if kind == 0xd0 and data:
        return f'Channel Pressure: {data[0]}'
    if kind == 0xa0 and len(data) >= 2:
        return f'Polyphonic Aftertouch: note {data[0]}, pressure {data[1]}'
    return event.description()
