"""Minimal Yamaha XG multipart model and standard Part parameter encoding.

Addresses follow XG Native Parameter Change multipart block 08 nn pp,
where nn is part number 00..0F. This intentionally covers only verified
single-byte fields; effects and voice catalogs are separate future work.
"""
from dataclasses import dataclass
from midi import MidiError
from xg_sysex import parameter_change, decode_parameter_change

# offset, minimum, maximum, default
PART_FIELDS = {
    "bank_msb": (0x01, 0, 127, 0),
    "bank_lsb": (0x02, 0, 127, 0),
    "program": (0x03, 0, 127, 0),  # MIDI program 0..127 (UI displays 1..128)
    "volume": (0x0b, 0, 127, 100),
    "pan": (0x0e, 0, 127, 64),
    "reverb_send": (0x13, 0, 127, 40),
    "chorus_send": (0x12, 0, 127, 0),
}
BY_OFFSET = {spec[0]: name for name, spec in PART_FIELDS.items()}

@dataclass
class Part:
    bank_msb: int = 0
    bank_lsb: int = 0
    program: int = 0
    volume: int = 100
    pan: int = 64
    reverb_send: int = 40
    chorus_send: int = 0

class XGParts:
    def __init__(self):
        self.parts = [Part() for _ in range(16)]

    def set(self, part, field, value):
        if not isinstance(part, int) or not 0 <= part < 16:
            raise MidiError("Part index must be 0..15")
        if field not in PART_FIELDS:
            raise MidiError("Unsupported XG Part parameter")
        _, low, high, _ = PART_FIELDS[field]
        if not isinstance(value, int) or not low <= value <= high:
            raise MidiError(f"{field} must be {low}..{high}")
        setattr(self.parts[part], field, value)

    def message(self, part, field, device=0):
        if not 0 <= part < 16 or field not in PART_FIELDS:
            raise MidiError("Invalid part or parameter")
        offset = PART_FIELDS[field][0]
        return parameter_change((0x08, part, offset),
                                (getattr(self.parts[part], field),), device)

    def apply_sysex(self, raw):
        decoded = decode_parameter_change(raw)
        if not decoded:
            return False
        a, part, offset = decoded["address"]
        field = BY_OFFSET.get(offset)
        if a != 0x08 or part > 15 or field is None or len(decoded["data"]) != 1:
            return False
        self.set(part, field, decoded["data"][0])
        return True
