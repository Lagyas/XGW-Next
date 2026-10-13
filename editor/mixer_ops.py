"""MIDI mixer operations: write channel controller values into SMF tracks."""
from midi import Event, MidiError

MIXER_CONTROLLERS = {"Volume": 7, "Pan": 10, "Expression": 11,
                     "Reverb": 91, "Chorus": 93}
MIXER_DEFAULTS = {"Volume": 100, "Pan": 64, "Expression": 127,
                  "Reverb": 40, "Chorus": 0}

def channel_values(song, channel, tick=0):
    if not 1 <= channel <= 16 or tick < 0:
        raise MidiError("Invalid channel or tick")
    result = dict(MIXER_DEFAULTS)
    lookup = {cc: name for name, cc in MIXER_CONTROLLERS.items()}
    events = []
    for track_index, track in enumerate(song.tracks):
        for event in track.events:
            if event.tick <= tick and event.status == (0xb0 | channel - 1) and len(event.data) == 2:
                events.append((event.tick, track_index, event.order, event))
    for _, _, _, event in sorted(events, key=lambda entry: entry[:3]):
        name = lookup.get(event.data[0])
        if name is not None:
            result[name] = event.data[1]
    return result

def set_channel_values(song, track_index, channel, values, tick=0):
    if not 0 <= track_index < len(song.tracks) or not 1 <= channel <= 16:
        raise MidiError("Invalid track or channel")
    if not 0 <= tick <= 0x0fffffff:
        raise MidiError("Invalid tick")
    if not values or any(name not in MIXER_CONTROLLERS or
                         type(value) is not int or not 0 <= value <= 127
                         for name, value in values.items()):
        raise MidiError("Invalid mixer value")
    track = song.tracks[track_index]
    status = 0xb0 | (channel - 1)
    next_order = max((event.order for event in track.events), default=-1) + 1
    for name, value in values.items():
        cc = MIXER_CONTROLLERS[name]
        existing = [event for event in track.events
                    if event.tick == tick and event.status == status
                    and len(event.data) == 2 and event.data[0] == cc]
        if existing:
            existing[-1].data = bytes((cc, value))
        else:
            track.events.append(Event(tick, status, bytes((cc, value)), order=next_order))
            next_order += 1
    song.dirty = True
    return len(values)
