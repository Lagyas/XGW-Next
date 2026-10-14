"""Atomic bulk edits for CC and pitch-bend events in a single MIDI track."""
from midi import MidiError


def bulk_controller_edit(song, track_index, indices, lane, channel, delta=0, delete=False):
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track index')
    if type(channel) is not int or not 1 <= channel <= 16:
        raise MidiError('MIDI channel must be 1–16')
    if lane != 'pitch' and (type(lane) is not int or not 0 <= lane <= 127):
        raise MidiError('Invalid controller lane')
    if type(delta) is not int or type(delete) is not bool:
        raise MidiError('Invalid bulk operation')
    events = song.tracks[track_index].events
    selected = set(indices)
    if not selected:
        return 0
    for i in selected:
        if type(i) is not int or not 0 <= i < len(events):
            raise MidiError('Invalid event index')
        e = events[i]
        if e.status != ((0xe0 if lane == 'pitch' else 0xb0) | (channel - 1)) or len(e.data) != 2 or (lane != 'pitch' and e.data[0] != lane):
            raise MidiError('Selected event does not belong to active controller lane/channel')
    changes = 0
    for i in sorted(selected, reverse=True):
        e = events[i]
        if delete:
            del events[i]
            changes += 1
        else:
            maximum = 16383 if lane == 'pitch' else 127
            old = (e.data[0] | (e.data[1] << 7)) if lane == 'pitch' else e.data[1]
            new = max(0, min(maximum, old + delta))
            data = bytes((new & 127, new >> 7)) if lane == 'pitch' else bytes((lane, new))
            if data != e.data:
                e.data = data
                changes += 1
    if changes:
        song.dirty = True
    return changes
