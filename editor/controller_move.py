"""Atomic tick relocation for selected MIDI CC or pitch-bend events."""
from midi import MidiError
from transport_ops import MAX_TICK


def move_controller_events(song, track_index, indices, lane, channel, delta):
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track index')
    if lane != 'pitch' and (type(lane) is not int or not 0 <= lane <= 127):
        raise MidiError('Invalid controller lane')
    if type(channel) is not int or not 1 <= channel <= 16:
        raise MidiError('MIDI channel must be 1–16')
    if type(delta) is not int:
        raise MidiError('Invalid time shift')
    events = song.tracks[track_index].events
    selected = set(indices)
    status = (0xe0 if lane == 'pitch' else 0xb0) | (channel - 1)
    for index in selected:
        if type(index) is not int or not 0 <= index < len(events):
            raise MidiError('Invalid event index')
        event = events[index]
        if event.status != status or len(event.data) != 2 or (lane != 'pitch' and event.data[0] != lane):
            raise MidiError('Selected event does not belong to active controller lane/channel')
        if not 0 <= event.tick + delta <= MAX_TICK:
            raise MidiError('Controller tick out of range')
    if delta == 0:
        return 0
    for index in selected:
        events[index].tick += delta
    if selected:
        song.dirty = True
    return len(selected)
