"""Edit MIDI control changes in a track without touching other events."""
from midi import Event, MidiError

CONTROLLERS = {
    1: "Modulation", 7: "Volume", 10: "Pan", 11: "Expression",
    64: "Sustain", 71: "Resonance", 74: "Brightness",
    91: "Reverb send", 93: "Chorus send",
}

def controller_events(song, track_index, channel=None, controller=None):
    if not 0 <= track_index < len(song.tracks):
        raise MidiError("Invalid track")
    result = []
    for index, event in enumerate(song.tracks[track_index].events):
        if event.status & 0xf0 != 0xb0 or len(event.data) != 2:
            continue
        if channel is not None and (event.status & 15) + 1 != channel:
            continue
        if controller is not None and event.data[0] != controller:
            continue
        result.append((index, event))
    return sorted(result, key=lambda item: (item[1].tick, item[1].order))

def set_controller(song, track_index, channel, controller, tick, value, event_index=None):
    if not 0 <= track_index < len(song.tracks):
        raise MidiError("Invalid track")
    if not 1 <= channel <= 16 or not 0 <= controller <= 127 or not 0 <= value <= 127:
        raise MidiError("Invalid channel, controller or value")
    if not 0 <= tick <= 0x0fffffff:
        raise MidiError("Invalid MIDI tick")
    track = song.tracks[track_index]
    if event_index is None:
        order = max((e.order for e in track.events), default=-1) + 1
        track.events.append(Event(tick, 0xb0 | (channel - 1),
                                  bytes((controller, value)), order=order))
        event_index = len(track.events) - 1
    else:
        if not 0 <= event_index < len(track.events):
            raise MidiError("Invalid event index")
        old = track.events[event_index]
        if old.status & 0xf0 != 0xb0 or len(old.data) != 2:
            raise MidiError("Selected event is not a control change")
        old.tick = tick
        old.status = 0xb0 | (channel - 1)
        old.data = bytes((controller, value))
    song.dirty = True
    return event_index

def delete_controller(song, track_index, event_index):
    if not 0 <= track_index < len(song.tracks):
        raise MidiError("Invalid track")
    track = song.tracks[track_index]
    if not 0 <= event_index < len(track.events):
        raise MidiError("Invalid event index")
    event = track.events[event_index]
    if event.status & 0xf0 != 0xb0 or len(event.data) != 2:
        raise MidiError("Selected event is not a control change")
    del track.events[event_index]
    song.dirty = True
