"""Shared, time-aware XG Part / MIDI mixer view (no implicit writes).

XG Part numbers and MIDI channels are both 1-based in the public API.
A channel/Part mapping is a user choice, not an assumption about multitimbral routing.
"""
from midi import MidiError, Event
from mixer_ops import MIXER_CONTROLLERS, MIXER_DEFAULTS
from xg_parts import PART_FIELDS
from xg_sysex import decode_parameter_change, smf_sysex_to_wire

FIELD_TO_MIXER = {"volume": "Volume", "pan": "Pan", "reverb_send": "Reverb",
                  "chorus_send": "Chorus", "variation_send": "Variation"}


def combined_part_values(song, part, channel, tick=0, device=0):
    """Return mixer values and source for latest CC or XG SysEx per parameter.

    Events are ordered by (tick, track, order, original index) to break ties.
    Only SysEx addressed to the selected device and Part can override CC.
    """
    if (type(part) is not int or not 1 <= part <= 16 or
        type(channel) is not int or not 1 <= channel <= 16 or
        type(tick) is not int or not 0 <= tick <= 0x0fffffff or
        type(device) is not int or not 0 <= device <= 15):
        raise MidiError("Invalid XG Part, channel, device or tick")
    values = dict(MIXER_DEFAULTS)
    sources = {name: "default" for name in values}
    cc_names = {number: name for name, number in MIXER_CONTROLLERS.items()}
    xg_names = {PART_FIELDS[field][0]: mixer for field, mixer in FIELD_TO_MIXER.items()}
    ordered = sorted((event.tick, track_index, event.order, index, event)
                     for track_index, track in enumerate(song.tracks)
                     for index, event in enumerate(track.events) if event.tick <= tick)
    for _, _, _, _, event in ordered:
        if event.status == 0xb0 | (channel - 1) and len(event.data) == 2:
            name = cc_names.get(event.data[0])
            if name is not None and event.data[1] <= 127:
                values[name], sources[name] = event.data[1], "CC"
        elif event.status in (0xf0, 0xf7):
            raw = smf_sysex_to_wire(event.status, event.data)
            decoded = decode_parameter_change(raw) if raw is not None else None
            if not decoded or decoded["device"] != device:
                continue
            a, p, offset = decoded["address"]
            if a == 0x08 and p == part - 1 and len(decoded["data"]) == 1:
                name = xg_names.get(offset)
                if name is not None:
                    values[name], sources[name] = decoded["data"][0], "XG SysEx"
    return values, sources


def write_xg_part_changes(song, track_index, part, changes, tick=0, device=0, replace=True):
    """Atomically write selected Part fields as Yamaha XG SysEx.

    Existing same-tick messages with identical device/Part/field are replaced.
    Unrelated messages (including other devices) remain byte-for-byte intact.
    """
    from xg_sysex import parameter_change
    if (type(track_index) is not int or not 0 <= track_index < len(song.tracks)
        or type(part) is not int or not 1 <= part <= 16
        or type(device) is not int or not 0 <= device <= 15
        or type(tick) is not int or not 0 <= tick <= 0x0fffffff
        or type(replace) is not bool or not isinstance(changes, dict) or not changes):
        raise MidiError("Invalid XG Part edit")
    messages = {}
    for field, value in changes.items():
        if (field not in PART_FIELDS or type(value) is not int
            or not PART_FIELDS[field][1] <= value <= PART_FIELDS[field][2]):
            raise MidiError("Invalid XG Part field or value")
        offset = PART_FIELDS[field][0]
        messages[offset] = parameter_change((0x08, part - 1, offset), (value,), device)
    track = song.tracks[track_index]
    retained = []
    for event in track.events:
        if replace and event.tick == tick and event.status in (0xf0, 0xf7):
            raw = smf_sysex_to_wire(event.status, event.data)
            decoded = decode_parameter_change(raw) if raw is not None else None
            if (decoded and decoded["device"] == device and
                decoded["address"][:2] == (0x08, part - 1) and
                decoded["address"][2] in messages):
                continue
        retained.append(event)
    order = max((event.order for event in retained), default=-1) + 1
    retained.extend(Event(tick, 0xf0, wire[1:], order=order + index)
                    for index, wire in enumerate(messages.values()))
    track.events[:] = retained
    song.dirty = True
    return len(messages)


def mixer_channel_snapshot(song, channel, assignment, tick=0):
    """Read the assigned Part/device for a *MIDI channel* (not a device-as-channel).

    The tuple contains (part, device), while combined_part_values expects
    (part, channel, tick, device). Keep that distinction in one tested place.
    """
    if (type(channel) is not int or not 1 <= channel <= 16 or
            not isinstance(assignment, (tuple, list)) or len(assignment) != 2):
        raise MidiError("Invalid mixer channel mapping")
    part, device = assignment
    return combined_part_values(song, part, channel, tick, device)


def mapped_mixer_snapshot(song, assignments, tick=0):
    """Read explicitly mapped MIDI channels and XG Parts/devices.

    assignments maps a 1-based MIDI channel to (1-based XG Part, device 0..15).
    No implicit mapping or output-port inference is performed.
    """
    if not isinstance(assignments, dict) or not assignments:
        raise MidiError("Specify MIDI channel to XG Part assignments")
    if type(tick) is not int or not 0 <= tick <= 0x0fffffff:
        raise MidiError("Invalid MIDI tick")
    for channel, mapping in assignments.items():
        if (type(channel) is not int or not 1 <= channel <= 16 or
            not isinstance(mapping, (tuple, list)) or len(mapping) != 2 or
            type(mapping[0]) is not int or not 1 <= mapping[0] <= 16 or
            type(mapping[1]) is not int or not 0 <= mapping[1] <= 15):
            raise MidiError("Invalid channel, Part or device mapping")
    return {channel: mixer_channel_snapshot(song, channel, (part, device), tick)
            for channel, (part, device) in assignments.items()}


def normalize_part_assignments(assignments):
    """Validate a complete 16-channel mixer to XG Part/device mapping."""
    if not isinstance(assignments, dict) or set(assignments) != set(range(1, 17)):
        raise MidiError("Provide an assignment for each MIDI channel 1–16")
    normalized = {}
    for channel, pair in assignments.items():
        if (not isinstance(pair, (tuple, list)) or len(pair) != 2
            or type(pair[0]) is not int or not 1 <= pair[0] <= 16
            or type(pair[1]) is not int or not 0 <= pair[1] <= 15):
            raise MidiError(f"Invalid XG mapping for channel {channel}")
        normalized[channel] = tuple(pair)
    return normalized


def default_part_assignments(device=0):
    if type(device) is not int or not 0 <= device <= 15:
        raise MidiError("XG device must be 0–15")
    return {channel: (channel, device) for channel in range(1, 17)}


def encode_part_assignments(assignments):
    """JSON-safe representation of the full mapping, validated before saving."""
    validated = normalize_part_assignments(assignments)
    return {str(channel): list(validated[channel]) for channel in range(1, 17)}


def decode_part_assignments(payload):
    """Read saved mapping; reject incomplete or malformed settings atomically."""
    if not isinstance(payload, dict):
        raise MidiError("Invalid saved XG mapping")
    if set(payload) != {str(ch) for ch in range(1, 17)}:
        raise MidiError("Invalid saved XG mapping")
    return normalize_part_assignments({ch: payload[str(ch)] for ch in range(1, 17)})


def channel_for_part(assignments, part, device):
    """Resolve an explicitly mapped channel for an XG Part/device.

    Returns None when the mapping is missing or ambiguous; never guesses a
    channel in a multiport arrangement.
    """
    if type(part) is not int or not 1 <= part <= 16 or type(device) is not int or not 0 <= device <= 15:
        raise MidiError("Invalid XG Part or device")
    if not isinstance(assignments, dict):
        raise MidiError("Invalid channel mapping")
    matching = []
    for channel, mapping in assignments.items():
        if (type(channel) is not int or not 1 <= channel <= 16 or
            not isinstance(mapping, (tuple, list)) or len(mapping) != 2 or
            type(mapping[0]) is not int or not 1 <= mapping[0] <= 16 or
            type(mapping[1]) is not int or not 0 <= mapping[1] <= 15):
            raise MidiError("Invalid channel mapping")
        if tuple(mapping) == (part, device):
            matching.append(channel)
    return matching[0] if len(matching) == 1 else None
