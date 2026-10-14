"""Per-track MIDI output routing. Channel numbers are zero-based on the wire."""
from midi import MidiError
from midi_output import tick_seconds, smf_sysex_to_wire


def validate_routes(song, routes, default_port):
    if not isinstance(default_port, str):
        raise MidiError('Invalid default MIDI output')
    if not isinstance(routes, dict):
        raise MidiError('Invalid track routing')
    result = {}
    for index, route in routes.items():
        if type(index) is not int or not 0 <= index < len(song.tracks):
            raise MidiError('Invalid routed track')
        if not isinstance(route, (list, tuple)) or len(route) != 2:
            raise MidiError('Route must contain output and channel override')
        port, channel = route
        if not isinstance(port, str) or not port.strip():
            raise MidiError('Invalid routed MIDI output')
        if channel is not None and (type(channel) is not int or not 0 <= channel < 16):
            raise MidiError('Invalid routed MIDI channel')
        result[index] = (port, channel)
    return result


def routed_messages(song, routes, default_port, start_tick=0, end_tick=None,
                    enabled_tracks=None, include_sysex=False):
    """Yield (relative seconds, port name, wire bytes), stable by tick/track/order."""
    routes = validate_routes(song, routes, default_port)
    if type(start_tick) is not int or start_tick < 0:
        raise MidiError('Invalid playback start tick')
    if end_tick is not None and (type(end_tick) is not int or end_tick <= start_tick):
        raise MidiError('Invalid playback end tick')
    if enabled_tracks is not None:
        from midi_output import validate_enabled_tracks
        enabled_tracks = validate_enabled_tracks(song, enabled_tracks)
    base = tick_seconds(song, start_tick)
    events = sorted(((ev.tick, i, ev.order, ev) for i, tr in enumerate(song.tracks)
                     if enabled_tracks is None or i in enabled_tracks for ev in tr.events),
                    key=lambda row: row[:3])
    for tick, index, _, event in events:
        if tick < start_tick or (end_tick is not None and tick >= end_tick):
            continue
        port, channel = routes.get(index, (default_port, None))
        if not port:
            raise MidiError('Choose an output for every playing track')
        if 0x80 <= event.status <= 0xef:
            status = event.status if channel is None else (event.status & 0xf0) | channel
            yield (tick_seconds(song, tick) - base, port, bytes([status]) + event.data)
        elif include_sysex and event.status == 0xf0:
            wire = smf_sysex_to_wire(event.status, event.data)
            if wire is not None:
                yield (tick_seconds(song, tick) - base, port, wire)
