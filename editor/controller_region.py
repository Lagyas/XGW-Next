"""Select MIDI controller event indices in an inclusive tick range."""
from midi import MidiError


def controller_indices_in_range(song, track_index, lane, channel, start_tick, end_tick):
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track index')
    if lane != 'pitch' and (type(lane) is not int or not 0 <= lane <= 127):
        raise MidiError('Invalid controller lane')
    if type(channel) is not int or not 1 <= channel <= 16:
        raise MidiError('MIDI channel must be 1–16')
    if any(type(t) is not int or t < 0 for t in (start_tick, end_tick)):
        raise MidiError('Invalid tick range')
    low, high = sorted((start_tick, end_tick))
    status = (0xe0 if lane == 'pitch' else 0xb0) | (channel - 1)
    return {i for i, event in enumerate(song.tracks[track_index].events)
            if low <= event.tick <= high and event.status == status
            and len(event.data) == 2 and (lane == 'pitch' or event.data[0] == lane)}
