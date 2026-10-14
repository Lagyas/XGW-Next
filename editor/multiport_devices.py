"""Map global MIDI channels to independent 16-channel physical endpoints.

A 32-channel device MUST expose two independently addressable output endpoints.
A single ordinary MIDI port cannot carry 32 independent channel addresses.
"""
from midi import MidiError


def validate_endpoints(endpoints, available=None):
    if not isinstance(endpoints, (list, tuple)) or not endpoints:
        raise MidiError('Choose at least one 16-channel MIDI output endpoint')
    if any(not isinstance(name, str) or not name.strip() for name in endpoints):
        raise MidiError('Invalid MIDI output endpoint')
    if len(set(endpoints)) != len(endpoints):
        raise MidiError('Each 16-channel bank requires a distinct MIDI output endpoint')
    if available is not None and any(name not in available for name in endpoints):
        raise MidiError('Selected MIDI output endpoint is not available')
    return tuple(endpoints)


def channel_destination(global_channel, endpoints):
    """Convert 1-based global channel to (physical endpoint name, 0-based wire channel)."""
    endpoints = validate_endpoints(endpoints)
    if type(global_channel) is not int or not 1 <= global_channel <= 16 * len(endpoints):
        raise MidiError('Global MIDI channel is outside configured output banks')
    return endpoints[(global_channel - 1) // 16], (global_channel - 1) % 16


def assign_global_channels(song, assignments, endpoints, available=None):
    """Build normal per-track routes for a multi-endpoint 32/64-channel device."""
    from midi_routing import validate_routes
    endpoints = validate_endpoints(endpoints, available)
    if not isinstance(assignments, dict):
        raise MidiError('Invalid track/channel assignments')
    routes = {}
    for track, global_channel in assignments.items():
        if type(track) is not int or not 0 <= track < len(song.tracks):
            raise MidiError('Invalid MIDI track')
        routes[track] = channel_destination(global_channel, endpoints)
    return validate_routes(song, routes, endpoints[0])
