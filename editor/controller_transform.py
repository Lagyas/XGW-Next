"""Validated atomic transforms of selected CC and pitch bend events."""
from copy import deepcopy
from uuid import uuid4
from midi import MidiError
from transport_ops import MAX_TICK


def transform_controllers(song, track_index, indices, lane, channel, tick_delta=0,
                          value_delta=0, copy=False):
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track index')
    if lane != 'pitch' and (type(lane) is not int or not 0 <= lane <= 127):
        raise MidiError('Invalid controller lane')
    if type(channel) is not int or not 1 <= channel <= 16:
        raise MidiError('Invalid MIDI channel')
    if type(tick_delta) is not int or type(value_delta) is not int or type(copy) is not bool:
        raise MidiError('Invalid controller transform')
    events = song.tracks[track_index].events
    selected = set(indices)
    if not selected or (tick_delta == 0 and value_delta == 0 and not copy):
        return 0, set()
    status = (0xE0 if lane == 'pitch' else 0xB0) | (channel - 1)
    maximum = 16383 if lane == 'pitch' else 127
    updates = []
    for index in sorted(selected):
        if type(index) is not int or not 0 <= index < len(events):
            raise MidiError('Invalid event index')
        event = events[index]
        if event.status != status or len(event.data) != 2 or (lane != 'pitch' and event.data[0] != lane):
            raise MidiError('Selected event does not belong to active lane/channel')
        tick = event.tick + tick_delta
        if not 0 <= tick <= MAX_TICK:
            raise MidiError('Controller tick out of range')
        old = event.data[0] | (event.data[1] << 7) if lane == 'pitch' else event.data[1]
        value = max(0, min(maximum, old + value_delta))
        data = bytes((value & 127, value >> 7)) if lane == 'pitch' else bytes((lane, value))
        updates.append((index, tick, data))
    changed = [(i, t, d) for i, t, d in updates if copy or events[i].tick != t or events[i].data != d]
    if not changed:
        return 0, selected
    if copy:
        new_indices = set()
        for i, tick, data in changed:
            clone = deepcopy(events[i]); clone.tick = tick; clone.data = data
            clone.uid = uuid4().hex
            clone.order = max((e.order for e in events), default=-1) + 1
            new_indices.add(len(events)); events.append(clone)
    else:
        for i, tick, data in changed:
            events[i].tick = tick; events[i].data = data
        new_indices = selected
    song.dirty = True
    return len(changed), new_indices
