"""Pitch-bend insertion/editing (14-bit MIDI values)."""
from midi import Event, MidiError


def insert_pitch_bend(song, track_index, tick, value, channel=1):
    if not isinstance(track_index, int) or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track index')
    if not isinstance(tick, int) or tick < 0:
        raise MidiError('Pitch bend tick must be nonnegative')
    if not isinstance(value, int) or not 0 <= value <= 16383:
        raise MidiError('Pitch bend value must be 0–16383')
    if not isinstance(channel, int) or not 1 <= channel <= 16:
        raise MidiError('MIDI channel must be 1–16')
    events = song.tracks[track_index].events
    status = 0xE0 + channel - 1
    data = bytes((value & 127, value >> 7))
    matches = [i for i, e in enumerate(events) if e.tick == tick and e.status == status and len(e.data) == 2]
    if matches:
        song.set_event(track_index, matches[-1], data=data)
        return False
    order = max((e.order for e in events if e.tick == tick), default=-1) + 1
    events.append(Event(tick, status, data, order=order))
    song.dirty = True
    return True
