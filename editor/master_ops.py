"""Master track tempo and time signature editing for Standard MIDI Files."""
from midi import Event, MidiError

def master_events(song):
    result = []
    for track_index, track in enumerate(song.tracks):
        for event_index, event in enumerate(track.events):
            if event.status == 0xff and event.meta_type in (0x51, 0x58):
                result.append((track_index, event_index, event))
    return sorted(result, key=lambda item: (item[2].tick, item[0], item[2].order))

def tempo_payload(bpm):
    if not 1 <= bpm <= 1000:
        raise MidiError("Tempo must be 1–1000 BPM")
    microseconds = round(60000000 / bpm)
    if not 1 <= microseconds <= 0xffffff:
        raise MidiError("Tempo cannot be represented in MIDI")
    return microseconds.to_bytes(3, "big")

def time_signature_payload(numerator, denominator):
    if not 1 <= numerator <= 255 or denominator not in (1, 2, 4, 8, 16, 32, 64):
        raise MidiError("Invalid time signature")
    return bytes((numerator, denominator.bit_length() - 1, 24, 8))

def put_master_event(song, tick, meta_type, data, track_index=0, event_index=None):
    if not song.tracks or not 0 <= track_index < len(song.tracks):
        raise MidiError("Invalid master track")
    if not 0 <= tick <= 0x0fffffff:
        raise MidiError("Invalid MIDI tick")
    if meta_type not in (0x51, 0x58):
        raise MidiError("Unsupported master event type")
    if len(data) != (3 if meta_type == 0x51 else 4):
        raise MidiError("Invalid master event payload")
    track = song.tracks[track_index]
    if event_index is None:
        order = max((event.order for event in track.events), default=-1) + 1
        track.events.append(Event(tick, 0xff, data, meta_type, order))
        event_index = len(track.events) - 1
    else:
        if not 0 <= event_index < len(track.events):
            raise MidiError("Invalid master event index")
        event = track.events[event_index]
        if event.status != 0xff or event.meta_type not in (0x51, 0x58):
            raise MidiError("Selected event is not a tempo or time signature")
        event.tick = tick
        event.meta_type = meta_type
        event.data = data
    song.dirty = True
    return event_index

def delete_master_event(song, track_index, event_index):
    if not 0 <= track_index < len(song.tracks):
        raise MidiError("Invalid master track")
    track = song.tracks[track_index]
    if not 0 <= event_index < len(track.events):
        raise MidiError("Invalid master event index")
    event = track.events[event_index]
    if event.status != 0xff or event.meta_type not in (0x51, 0x58):
        raise MidiError("Not a master event")
    del track.events[event_index]
    song.dirty = True
