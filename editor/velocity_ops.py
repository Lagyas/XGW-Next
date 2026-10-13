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
