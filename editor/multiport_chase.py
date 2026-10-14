"""Reconstruct per-output MIDI controller state at a transport seek position."""
from midi_routing import validate_routes
from midi import MidiError

CHASE_CONTROLLERS = frozenset((0, 1, 7, 10, 11, 32, 64, 65, 66, 67, 91, 93, 94))

def chase_messages(song, routes, default_port, tick, enabled_tracks=None):
    """Return ordered (port, wire message) for the state immediately before tick.

    Controllers and program changes are reconstructed; notes are deliberately
    excluded to avoid triggering stuck notes when seeking into a passage.
    """
    if type(tick) is not int or tick < 0:
        raise MidiError('Invalid chase tick')
    resolved = validate_routes(song, routes, default_port)
    if enabled_tracks is not None:
        from midi_output import validate_enabled_tracks
        enabled_tracks = validate_enabled_tracks(song, enabled_tracks)
    state = {}
    for index, track in enumerate(song.tracks):
        if enabled_tracks is not None and index not in enabled_tracks:
            continue
        port, override = resolved.get(index, (default_port, None))
        for event in sorted(track.events, key=lambda e: (e.tick, e.order)):
            if event.tick >= tick:
                break
            status = event.status
            if not 0x80 <= status <= 0xef:
                continue
            channel = status & 15 if override is None else override
            kind = status & 0xf0
            if kind == 0xb0 and len(event.data) >= 2 and event.data[0] in CHASE_CONTROLLERS:
                state[(port, channel, 'cc', event.data[0])] = bytes([0xb0 | channel]) + event.data[:2]
            elif kind == 0xc0 and event.data:
                state[(port, channel, 'program', 0)] = bytes([0xc0 | channel, event.data[0]])
    priority = lambda key: (key[0], key[1], 0 if key[2] == 'cc' and key[3] == 0 else 1 if key[2] == 'cc' and key[3] == 32 else 2 if key[2] == 'program' else 3, key[3])
    return [(key[0], state[key]) for key in sorted(state, key=priority)]
