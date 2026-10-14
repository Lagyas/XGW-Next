"""Validated, explicit application of XG effect snapshot values to a song."""
from midi import MidiError
from xg_effects import EFFECT_TYPE_ADDRESSES, write_effect_parameter_to_song


def apply_snapshot_parameter(song, snapshot, effect, offset, tick, track_index=0, device=0):
    """Insert one selected snapshot value; never mutate on invalid input."""
    if not isinstance(snapshot, dict) or effect not in EFFECT_TYPE_ADDRESSES:
        raise MidiError('Invalid effect snapshot')
    if type(offset) is not int or not 0 <= offset < 32:
        raise MidiError('Invalid effect offset')
    key = (effect, offset)
    if key not in snapshot:
        raise MidiError('Parameter is absent from snapshot')
    return write_effect_parameter_to_song(song, effect, offset, snapshot[key], tick,
                                          track_index=track_index, device=device)


def apply_snapshot_batch(song, snapshot, selections, tick, track_index=0, device=0,
                         replace=False):
    """Atomically insert selected XG values, optionally replacing matching events.

    All inputs and messages are validated before the track is modified.
    """
    from xg_effects import effect_parameter_message, EFFECT_TYPE_ADDRESSES
    from xg_sysex import smf_sysex_to_wire, decode_parameter_change
    from midi import Event
    if type(tick) is not int or tick < 0 or type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid destination')
    if type(device) is not int or not 0 <= device <= 15 or type(replace) is not bool:
        raise MidiError('Invalid XG device or replace option')
    if not isinstance(snapshot, dict) or not isinstance(selections, (list, tuple)) or not selections:
        raise MidiError('Select at least one XG parameter')
    messages = []
    addresses = set()
    for key in selections:
        if not isinstance(key, tuple) or len(key) != 2 or key in addresses:
            raise MidiError('Invalid or duplicate XG selection')
        effect, offset = key
        if effect not in EFFECT_TYPE_ADDRESSES or type(offset) is not int or not 0 <= offset < 32 or key not in snapshot:
            raise MidiError('Unknown XG parameter')
        wire = effect_parameter_message(effect, offset, snapshot[key], device)
        messages.append(wire)
        addresses.add(key)
    track = song.tracks[track_index]
    retained = []
    for event in track.events:
        if replace and event.tick == tick and event.status in (0xf0, 0xf7):
            wire = smf_sysex_to_wire(event.status, event.data)
            decoded = decode_parameter_change(wire) if wire is not None else None
            if decoded is not None and decoded['device'] == device:
                address = decoded['address']
                for effect, offset in addresses:
                    base = EFFECT_TYPE_ADDRESSES[effect]
                    if address == (base[0], base[1], base[2] + offset):
                        break
                else:
                    retained.append(event)
                continue
        retained.append(event)
    order = max((event.order for event in retained), default=-1) + 1
    retained.extend(Event(tick, 0xf0, wire[1:], order=order + i)
                    for i, wire in enumerate(messages))
    track.events[:] = retained
    song.dirty = True
    return len(messages)
