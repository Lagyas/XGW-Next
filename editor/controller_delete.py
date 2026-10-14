"""Safe removal of a single Piano Roll controller event."""
from midi import MidiError


def delete_controller(song, track_index, event_index, lane):
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track index')
    events = song.tracks[track_index].events
    if type(event_index) is not int or not 0 <= event_index < len(events):
        raise MidiError('Invalid event index')
    event = events[event_index]
    if lane == 'pitch':
        valid = event.status & 0xf0 == 0xe0 and len(event.data) == 2
    elif type(lane) is int and 0 <= lane <= 127:
        valid = event.status & 0xf0 == 0xb0 and len(event.data) == 2 and event.data[0] == lane
    else:
        raise MidiError('Invalid controller lane')
    if not valid:
        raise MidiError('Selected event is not in the active controller lane')
    del events[event_index]
    song.dirty = True
