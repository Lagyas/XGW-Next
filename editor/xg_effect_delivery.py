"""Validated, route-aware XG effect delivery; real ports require hardware QA."""
from midi import MidiError
from xg_sysex import smf_sysex_to_wire

def resolve_effect_port(app, track_index):
    if type(track_index) is not int or track_index < 0:
        raise MidiError("Select a valid MIDI track for XG effect routing")
    routes = getattr(app, "track_routes", None) or {}
    default = app.output_name.get()
    port = routes.get(track_index, (default, None))[0]
    if not isinstance(port, str) or not port.strip():
        raise MidiError("Choose an active MIDI output for this track")
    return port

def deliver_effect_messages(app, track_index, messages):
    """Send validated complete SysEx messages via active player or closed output.

    Does not claim atomic delivery: hardware may disconnect mid-batch.
    """
    port = resolve_effect_port(app, track_index)
    if not isinstance(messages, (list, tuple)) or not messages:
        raise MidiError("No XG effect messages")
    payloads = []
    for wire in messages:
        if not isinstance(wire, (bytes, bytearray)) or len(wire) < 3 or wire[0] != 0xf0 or wire[-1] != 0xf7 or any(b > 127 for b in wire[1:-1]):
            raise MidiError("Invalid complete 7-bit SysEx message")
        payloads.append(bytes(wire))
    if app.player.playing:
        if not getattr(app, 'track_routes', None):
            raise MidiError("Stop single-port playback before sending effects")
        for wire in payloads:
            if not app.player.send_routed_sysex(port, wire):
                raise MidiError("Routed MIDI output is not active")
        return port, 'queued'
    import mido
    with mido.open_output(port) as output:
        for wire in payloads:
            output.send(mido.Message('sysex', data=list(wire[1:-1])))
    return port, 'sent'
