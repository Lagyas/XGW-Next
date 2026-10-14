"""Reconstruct held MIDI notes at a paused transport cursor.

Only key-held notes are restored. Pedal-latched and SysEx-driven voices are
intentionally excluded; normal future note-offs release restored notes.
"""
from collections import defaultdict, deque
from midi import MidiError


def held_notes(song, tick, routes=None, default_port=None, enabled_tracks=None,
               enabled_channels=None):
    """Return (port, note-on bytes) for keys held across ``tick``.

    Each note-on is paired with a note-off on the same routed port/channel/key.
    Multiple overlapping strikes of one key are paired FIFO. Events at the
    cursor are not chased: they will be played by the normal timeline.
    """
    if type(tick) is not int or not 0 <= tick <= 0x0fffffff:
        raise MidiError('Invalid note chase tick')
    from midi_output import validate_enabled_tracks, validate_enabled_channels
    selected = validate_enabled_tracks(song, enabled_tracks)
    channels = (None if enabled_channels is None else validate_enabled_channels(enabled_channels))
    if routes is not None:
        from midi_routing import validate_routes
        routes = validate_routes(song, routes, default_port)
    active = defaultdict(deque)
    events = sorted(((ev.tick, index, ev.order, ev)
                     for index, track in enumerate(song.tracks)
                     if selected is None or index in selected
                     for ev in track.events if ev.tick < tick), key=lambda item: item[:3])
    for _, index, _, ev in events:
        kind = ev.status & 0xf0
        if not 0x80 <= ev.status <= 0xef or kind not in (0x80, 0x90) or len(ev.data) < 2:
            continue
        port, override = (routes.get(index, (default_port, None)) if routes is not None
                          else (default_port, None))
        channel = ev.status & 15 if override is None else override
        if channels is not None and channel not in channels:
            continue
        key = (port, channel, ev.data[0])
        if kind == 0x90 and ev.data[1] > 0:
            active[key].append(bytes((0x90 | channel, ev.data[0], ev.data[1])))
        elif active[key]:
            active[key].popleft()
    return [(port, payload) for key in sorted(active) for payload in active[key]]
