"""Atomic Event List operations using original track/event indices.

A selection is resolved before mutation. Events may be shifted or duplicated;
non-note channel messages and SysEx are supported without interpreting payloads.
"""
from copy import deepcopy
from uuid import uuid4
from midi import Event, MidiError

MAX_TICK = 0x0fffffff

def edit_events(song, selections, delta=0, duplicate=False, destination_track=None):
    """Move/copy selected events; return event count. No partial writes on error."""
    if type(delta) is not int:
        raise MidiError('Tick offset must be an integer')
    selections = list(selections)
    if not selections or len(set(selections)) != len(selections):
        raise MidiError('Empty or duplicate event selection')
    if destination_track is not None and (type(destination_track) is not int or
            not 0 <= destination_track < len(song.tracks)):
        raise MidiError('Invalid destination track')
    if not 0 < song.division < 0x8000:
        raise MidiError('Only PPQN MIDI is supported')
    actions = []
    for track_idx, event_idx in selections:
        if (type(track_idx) is not int or type(event_idx) is not int or
                not 0 <= track_idx < len(song.tracks) or
                not 0 <= event_idx < len(song.tracks[track_idx].events)):
            raise MidiError('Invalid event selection')
        event = song.tracks[track_idx].events[event_idx]
        if event.status == 0xff and event.meta_type in (0x2f, 0x51, 0x58, 0x59):
            raise MidiError('Structural MIDI events cannot be moved by batch edit')
        tick = event.tick + delta
        if not 0 <= tick <= MAX_TICK:
            raise MidiError('MIDI tick exceeds supported range')
        dest = track_idx if destination_track is None else destination_track
        actions.append((track_idx, event_idx, dest, tick))
    staged = deepcopy(song.tracks)
    next_order = [max((e.order for e in tr.events), default=-1) + 1 for tr in staged]
    removals = {}
    for source, index, dest, tick in actions:
        if duplicate or dest != source:
            e = song.tracks[source].events[index]
            staged[dest].events.append(Event(tick, e.status, bytes(e.data), e.meta_type, next_order[dest],
                                             uid=e.uid if not duplicate else uuid4().hex))
            next_order[dest] += 1
            if not duplicate:
                removals.setdefault(source, set()).add(index)
        else:
            staged[source].events[index].tick = tick
    for source, indices in removals.items():
        staged[source].events = [e for i,e in enumerate(staged[source].events) if i not in indices]
    song.tracks = staged
    song.dirty = True
    return len(actions)
