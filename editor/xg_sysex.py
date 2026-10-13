"""Yamaha XG System Exclusive helpers.

XG parameter change format: F0 43 1n 4C aa aa aa data... F7
where n is device number (0..15). This is not a checksum format.
"""
from midi import MidiError

XG_MODEL_ID = 0x4c
YAMAHA_ID = 0x43
XG_SYSTEM_ON_ADDRESS = (0x00, 0x00, 0x7e)
XG_SYSTEM_ON_DATA = (0x00,)

def _u7(value, name):
    if not isinstance(value, int) or not 0 <= value <= 127:
        raise MidiError(f"{name} must be 0..127")
    return value

def parameter_change(address, data, device=0):
    if len(address) != 3 or not data:
        raise MidiError("XG address must be 3 bytes and data must not be empty")
    _u7(device, "Device number")
    if device > 15:
        raise MidiError("XG device number must be 0..15")
    payload = [_u7(v, "Address") for v in address]
    payload += [_u7(v, "Data") for v in data]
    return bytes((0xf0, YAMAHA_ID, 0x10 | device, XG_MODEL_ID, *payload, 0xf7))

def system_on(device=0):
    return parameter_change(XG_SYSTEM_ON_ADDRESS, XG_SYSTEM_ON_DATA, device)

def decode_parameter_change(raw):
    """Decode a complete XG parameter change, or return None for other SysEx."""
    if (len(raw) < 9 or raw[0] != 0xf0 or raw[-1] != 0xf7
            or raw[1] != YAMAHA_ID or raw[3] != XG_MODEL_ID
            or raw[2] & 0xf0 != 0x10):
        return None
    if any(v > 127 for v in raw[1:-1]):
        return None
    return {
        "device": raw[2] & 0x0f,
        "address": tuple(raw[4:7]),
        "data": bytes(raw[7:-1]),
    }

def smf_sysex_to_wire(status, data):
    """Convert SMF F0/F7 payload to a complete F0...F7 wire message.

    SMF F0 stores bytes *after* F0. F7 continuation/escape events are not
    standalone messages and are deliberately not sent without reassembly.
    """
    if status != 0xf0:
        return None
    if not data or data[-1] != 0xf7:
        return None
    if any(byte > 127 for byte in data[:-1]):
        return None
    return bytes((0xf0,)) + data

def is_xg_system_on(raw):
    decoded = decode_parameter_change(raw)
    return decoded is not None and decoded["address"] == XG_SYSTEM_ON_ADDRESS and decoded["data"] == b"\x00"
