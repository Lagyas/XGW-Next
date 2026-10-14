"""Velocity editing for paired MIDI notes, without changing note timing."""
from midi import MidiError
from note_ops import paired_notes

def set_note_velocities(song, track_index, velocities):
    """Update note-on velocity for {on_event_index: velocity}; atomic validation."""
    if not 0 <= track_index < len(song.tracks):
        raise MidiError("Invalid track")
    track = song.tracks[track_index]
    valid = {on for on, _ in paired_notes(track)}
    if not velocities or any(index not in valid or type(value) is not int or
                             not 1 <= value <= 127 for index, value in velocities.items()):
        raise MidiError("Invalid note or velocity")
    for index, velocity in velocities.items():
        event = track.events[index]
        event.data = bytes((event.data[0], velocity))
    song.dirty = True
    return len(velocities)


def scale_note_velocities(song, track_index, on_indices, percent, offset=0):
    """Scale selected note-on velocities, clamp 1..127, validate atomically."""
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track')
    if type(percent) is not int or not 0 <= percent <= 400 or type(offset) is not int or not -127 <= offset <= 127:
        raise MidiError('Invalid velocity transform')
    chosen = list(on_indices)
    valid = {a for a,_ in paired_notes(song.tracks[track_index])}
    if not chosen or len(set(chosen)) != len(chosen) or any(type(i) is not int or i not in valid for i in chosen):
        raise MidiError('Invalid note selection')
    changes = {}
    for i in chosen:
        old = song.tracks[track_index].events[i].data[1]
        changes[i] = max(1,min(127,(old * percent + 50)//100 + offset))
    if all(song.tracks[track_index].events[i].data[1] == value for i,value in changes.items()):
        return 0
    for i,value in changes.items():
        event = song.tracks[track_index].events[i]
        event.data = bytes((event.data[0],value))
    song.dirty = True
    return len(changes)
