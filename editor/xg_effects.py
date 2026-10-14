"""Yamaha XG System Effects type selectors (Native Parameter Change).

Only effect type MSB/LSB pairs are covered. Parameter blocks, insertion
routing and per-algorithm parameters are deliberately out of scope.
"""
from dataclasses import dataclass, field
from midi import MidiError, Event
from xg_sysex import parameter_change, decode_parameter_change, smf_sysex_to_wire

# XG native system effects: 02 01 xx
EFFECT_TYPE_ADDRESSES = {
    'reverb': (0x02, 0x01, 0x00),
    'chorus': (0x02, 0x01, 0x20),
    'variation': (0x02, 0x01, 0x40),
}


def _byte(value):
    if type(value) is not int or not 0 <= value <= 127:
        raise MidiError('XG effect type bytes must be integers 0–127')
    return value


@dataclass
class XGEffects:
    types: dict = field(default_factory=lambda: {
        'reverb': (1, 0), 'chorus': (65, 0), 'variation': (0, 0)
    })

    def set_type(self, effect, msb, lsb):
        if effect not in EFFECT_TYPE_ADDRESSES:
            raise MidiError('Unsupported XG system effect')
        self.types[effect] = (_byte(msb), _byte(lsb))

    def message(self, effect, device=0):
        if effect not in EFFECT_TYPE_ADDRESSES:
            raise MidiError('Unsupported XG system effect')
        return parameter_change(EFFECT_TYPE_ADDRESSES[effect], self.types[effect], device)

    def apply_sysex(self, raw, device=None):
        if device is not None and (type(device) is not int or not 0 <= device <= 15):
            raise MidiError("XG device must be 0–15")
        decoded = decode_parameter_change(raw)
        if (not decoded or len(decoded['data']) != 2
                or (device is not None and decoded['device'] != device)):
            return False
        for effect, address in EFFECT_TYPE_ADDRESSES.items():
            if decoded['address'] == address:
                self.set_type(effect, *decoded['data'])
                return True
        return False


def effects_from_song(song, through_tick=None, device=None):
    if through_tick is not None and (type(through_tick) is not int or through_tick < 0):
        raise MidiError('Position must be a non-negative integer')
    if device is not None and (type(device) is not int or not 0 <= device <= 15):
        raise MidiError("XG device must be 0–15")
    model = XGEffects()
    events = sorted(((event.tick, ti, event.order, index, event)
                     for ti, track in enumerate(song.tracks)
                     for index, event in enumerate(track.events)
                     if event.status in (0xf0, 0xf7)
                     and (through_tick is None or event.tick <= through_tick)),
                    key=lambda item: item[:4])
    count = 0
    for _, _, _, _, event in events:
        wire = smf_sysex_to_wire(event.status, event.data)
        if wire is not None and model.apply_sysex(wire, device=device):
            count += 1
    return model, count


def write_effect_types_to_song(song, model, tick, track_index=0, device=0, replace=False):
    """Insert three XG effect type SysEx messages at a song position.

    By default preserves existing events. With replace=True, removes only
    matching effect-type messages at the same tick, track and device.
    Validation is atomic.
    The messages are stored as SMF F0 payloads without the leading F0.
    """
    if type(tick) is not int or tick < 0:
        raise MidiError('Position must be a non-negative integer')
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track index')
    if type(device) is not int or not 0 <= device <= 15:
        raise MidiError('XG device must be 0–15')
    if not isinstance(model, XGEffects):
        raise MidiError('Invalid XG effects model')
    if type(replace) is not bool:
        raise MidiError('Replace must be a boolean')
    # Validate and build all messages before mutating the song.
    messages = [model.message(effect, device) for effect in EFFECT_TYPE_ADDRESSES]
    track = song.tracks[track_index]
    if replace:
        addresses = set(EFFECT_TYPE_ADDRESSES.values())
        retained = []
        for event in track.events:
            if event.tick != tick or event.status != 0xf0:
                retained.append(event)
                continue
            wire = smf_sysex_to_wire(event.status, event.data)
            decoded = decode_parameter_change(wire) if wire is not None else None
            if (decoded is None or decoded['device'] != device
                    or decoded['address'] not in addresses
                    or len(decoded['data']) != 2):
                retained.append(event)
        track.events[:] = retained
    next_order = max((e.order for e in track.events), default=-1) + 1
    track.events.extend(Event(tick, 0xf0, wire[1:], order=next_order + i)
                        for i, wire in enumerate(messages))
    song.dirty = True
    return len(messages)


def inspect_effect_parameter_changes(song, through_tick=None, device=None):
    """Inspect raw XG system-effect parameter changes without guessing meanings.

    Returns (tick, track_index, effect, address, data) tuples. The native
    XG system-effect blocks occupy 02 01 00..1F (reverb), 20..3F (chorus),
    and 40..5F (variation). This deliberately does not assign parameter
    names, units or supported ranges to model-specific offsets.
    """
    if through_tick is not None and (type(through_tick) is not int or through_tick < 0):
        raise MidiError('Position must be a non-negative integer')
    if device is not None and (type(device) is not int or not 0 <= device <= 15):
        raise MidiError('XG device must be 0–15')
    result = []
    for track_index, track in enumerate(song.tracks):
        for index, event in enumerate(track.events):
            if event.status != 0xf0 or (through_tick is not None and event.tick > through_tick):
                continue
            wire = smf_sysex_to_wire(event.status, event.data)
            decoded = decode_parameter_change(wire) if wire is not None else None
            if decoded is None or (device is not None and decoded['device'] != device):
                continue
            a, b, offset = decoded['address']
            if a != 0x02 or b != 0x01 or not 0 <= offset < 0x60:
                continue
            effect = ('reverb', 'chorus', 'variation')[offset // 0x20]
            result.append((event.tick, track_index, effect,
                           decoded['address'], decoded['data'], event.order, index))
    result.sort(key=lambda x: (x[0], x[1], x[5], x[6]))
    return [(tick, track, effect, address, data)
            for tick, track, effect, address, data, _, _ in result]


def format_effect_parameter_row(row):
    """Format an inspected raw parameter without guessing model-specific semantics."""
    tick, track, effect, address, data = row
    if type(tick) is not int or tick < 0 or type(track) is not int or track < 0:
        raise MidiError('Invalid inspected effect position')
    if effect not in EFFECT_TYPE_ADDRESSES or not isinstance(address, (tuple, list)) or len(address) != 3 or any(
            type(v) is not int or not 0 <= v <= 127 for v in address):
        raise MidiError('Invalid inspected effect address')
    if not isinstance(data, (bytes, bytearray)) or not data or any(v > 127 for v in data):
        raise MidiError('Invalid inspected effect data')
    offset = address[2] - EFFECT_TYPE_ADDRESSES[effect][2]
    if not 0 <= offset < 0x20 or address[:2] != (2, 1):
        raise MidiError('Address does not belong to effect block')
    if offset == 0 and len(data) != 2:
        raise MidiError('Effect Type requires exactly two bytes')
    parameter = 'Effect Type' if offset == 0 else f'Parameter +{offset:02X}'
    return (str(tick), str(track + 1), effect.title(), parameter,
            ' '.join(f'{v:02X}' for v in address), ' '.join(f'{v:02X}' for v in data))


def write_effect_parameter_to_song(song, effect, offset, values, tick,
                                   track_index=0, device=0, replace=False):
    """Write a raw XG system-effect parameter, without guessing its semantics.

    Replacement only targets the exact address, device, tick and track.
    Validation finishes before any existing MIDI events are modified.
    """
    if effect not in EFFECT_TYPE_ADDRESSES:
        raise MidiError('Unsupported XG system effect')
    if type(offset) is not int or not 0 <= offset < 0x20:
        raise MidiError('Effect parameter offset must be 0–31')
    if type(tick) is not int or tick < 0:
        raise MidiError('Position must be a non-negative integer')
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track index')
    if type(device) is not int or not 0 <= device <= 15:
        raise MidiError('XG device must be 0–15')
    if type(replace) is not bool:
        raise MidiError('Replace must be a boolean')
    if not isinstance(values, (bytes, bytearray, tuple, list)) or not values:
        raise MidiError('Parameter values must be nonempty 7-bit bytes')
    if any(type(v) is not int or not 0 <= v <= 127 for v in values):
        raise MidiError('Parameter values must be 7-bit bytes')
    if offset == 0 and len(values) != 2:
        raise MidiError('Effect Type requires exactly two bytes')
    address = (*EFFECT_TYPE_ADDRESSES[effect][:2],
               EFFECT_TYPE_ADDRESSES[effect][2] + offset)
    wire = parameter_change(address, values, device)
    track = song.tracks[track_index]
    retained = []
    for event in track.events:
        if not replace or event.tick != tick or event.status != 0xf0:
            retained.append(event)
            continue
        raw = smf_sysex_to_wire(event.status, event.data)
        decoded = decode_parameter_change(raw) if raw is not None else None
        if decoded is None or decoded['device'] != device or decoded['address'] != address:
            retained.append(event)
    order = max((event.order for event in retained), default=-1) + 1
    retained.append(Event(tick, 0xf0, wire[1:], order=order))
    track.events[:] = retained
    song.dirty = True
    return 1


def effect_parameter_message(effect, offset, values, device=0):
    """Build a validated XG effect parameter message for live MIDI output.

    This does not modify a song or infer undocumented parameter semantics.
    """
    if effect not in EFFECT_TYPE_ADDRESSES:
        raise MidiError('Unsupported XG system effect')
    if type(offset) is not int or not 0 <= offset < 0x20:
        raise MidiError('Effect parameter offset must be 0–31')
    if not isinstance(values, (bytes, bytearray, tuple, list)) or not values:
        raise MidiError('Parameter values must be nonempty 7-bit bytes')
    if any(type(v) is not int or not 0 <= v <= 127 for v in values):
        raise MidiError('Parameter values must be 7-bit bytes')
    if offset == 0 and len(values) != 2:
        raise MidiError('Effect Type requires exactly two bytes')
    base = EFFECT_TYPE_ADDRESSES[effect]
    return parameter_change((base[0], base[1], base[2] + offset), values, device)


def effect_parameters_at_tick(song, tick, device=0, effect=None):
    """Return the last XG effect parameter values effective at a song position.

    Keys are (effect name, block-relative offset); values are raw bytes.
    This is a read-only snapshot, not a hardware state query.
    """
    if type(tick) is not int or tick < 0:
        raise MidiError('Position must be a non-negative integer')
    if type(device) is not int or not 0 <= device <= 15:
        raise MidiError('XG device must be 0–15')
    if effect is not None and effect not in EFFECT_TYPE_ADDRESSES:
        raise MidiError('Unsupported XG system effect')
    snapshot = {}
    for _, _, name, address, data in inspect_effect_parameter_changes(song, through_tick=tick, device=device):
        if effect is None or effect == name:
            snapshot[(name, address[2] - EFFECT_TYPE_ADDRESSES[name][2])] = bytes(data)
    return snapshot


def describe_effect_parameter(row):
    """Human-readable description for XG effect inspector without changing its raw columns."""
    fields = format_effect_parameter_row(row)
    _, _, effect, address, data = row
    base = EFFECT_TYPE_ADDRESSES[effect]
    if address[2] == base[2]:
        from xg_effect_catalog import effect_type_name
        return 'Effect Type — ' + effect_type_name(effect, data[0], data[1])
    return fields[3]
