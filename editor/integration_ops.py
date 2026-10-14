"""Validated, atomic MIDI editing primitives shared by piano roll and sequencer."""
from copy import deepcopy
from midi import Event, MidiError

MAX_TICK = 0x0fffffff

def _selection(song, track_index, event_indices):
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track')
    if not isinstance(event_indices, (list, tuple, set)) or any(type(i) is not int or not 0 <= i < len(song.tracks[track_index].events) for i in event_indices):
        raise MidiError('Invalid event selection')
    if len(set(event_indices)) != len(event_indices):
        raise MidiError('Duplicate event selection')
    return [song.tracks[track_index].events[i] for i in event_indices]

def move_events(song, track_index, event_indices, delta_ticks=0, semitones=0, copy=False):
    """Move/copy selected events without partially editing on failure.

    Pitch change applies only to note-on/off and polyphonic aftertouch.
    Callers must select both ends of a note to retain its duration.
    """
    events = _selection(song, track_index, event_indices)
    if type(delta_ticks) is not int or type(semitones) is not int or type(copy) is not bool:
        raise MidiError('Invalid edit arguments')
    if any(e.status == 0xff and e.meta_type == 0x2f for e in events):
        raise MidiError('End-of-track cannot be moved')
    changed = []
    for event in events:
        tick = event.tick + delta_ticks
        if not 0 <= tick <= MAX_TICK:
            raise MidiError('Event outside MIDI tick range')
        data = event.data
        if event.status & 0xf0 in (0x80, 0x90, 0xa0) and event.status < 0xf0:
            if not data or not 0 <= data[0] + semitones <= 127:
                raise MidiError('Note outside MIDI pitch range')
            data = bytes((data[0] + semitones,)) + data[1:]
        changed.append((tick, data))
    if not events or (not copy and not delta_ticks and not semitones):
        return 0
    if copy:
        next_order = max((e.order for e in song.tracks[track_index].events), default=-1) + 1
        for event, (tick, data) in zip(events, changed):
            song.tracks[track_index].events.append(Event(tick, event.status, data, event.meta_type, next_order))
            next_order += 1
    else:
        for event, (tick, data) in zip(events, changed):
            event.tick, event.data = tick, data
    song.dirty = True
    return len(events)

def transfer_events(song, source_track, event_indices, destination_track, delta_ticks=0, copy=False):
    """Move/copy events between tracks; validate before modifying either track."""
    events = _selection(song, source_track, event_indices)
    if type(destination_track) is not int or not 0 <= destination_track < len(song.tracks):
        raise MidiError('Invalid destination track')
    if type(delta_ticks) is not int or type(copy) is not bool:
        raise MidiError('Invalid transfer arguments')
    if source_track == destination_track:
        return move_events(song, source_track, event_indices, delta_ticks, copy=copy)
    if any(e.status == 0xff and e.meta_type == 0x2f or not 0 <= e.tick + delta_ticks <= MAX_TICK for e in events):
        raise MidiError('Invalid transferred event')
    if not events:
        return 0
    target = song.tracks[destination_track].events
    order = max((e.order for e in target), default=-1) + 1
    for e in events:
        target.append(Event(e.tick + delta_ticks, e.status, e.data, e.meta_type, order))
        order += 1
    if not copy:
        ids = {id(e) for e in events}
        song.tracks[source_track].events[:] = [e for e in song.tracks[source_track].events if id(e) not in ids]
    song.dirty = True
    return len(events)
