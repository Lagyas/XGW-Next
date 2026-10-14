"""Validated controller-lane event insertion for Piano Roll."""
from midi import Event, MidiError


def insert_cc(song, track_index, tick, controller, value, channel=1):
    if not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track index')
    if not isinstance(tick, int) or tick < 0:
        raise MidiError('CC tick must be nonnegative')
    if not isinstance(controller, int) or not 0 <= controller <= 127:
        raise MidiError('CC controller must be 0–127')
    if not isinstance(value, int) or not 0 <= value <= 127:
        raise MidiError('CC value must be 0–127')
    if not isinstance(channel, int) or not 1 <= channel <= 16:
        raise MidiError('MIDI channel must be 1–16')
    events = song.tracks[track_index].events
    matches = [i for i, e in enumerate(events) if e.tick == tick and e.status == 0xB0 + channel - 1 and len(e.data) == 2 and e.data[0] == controller]
    if matches:
        song.set_event(track_index, matches[-1], data=bytes((controller, value)))
        return False
    order = max((e.order for e in events if e.tick == tick), default=-1) + 1
    events.append(Event(tick, 0xB0 + channel - 1, bytes((controller, value)), order=order))
    song.dirty = True
    return True
