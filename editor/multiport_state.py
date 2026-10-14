"""Validated, portable MIDI routing sidecar and independent port monitor masks."""
import json
from pathlib import Path
from midi import MidiError
from midi_routing import validate_routes


def effective_port_channels(port, muted, solo):
    if not isinstance(port, str) or not port.strip():
        raise MidiError('Invalid MIDI port')
    if any(type(ch) is not int or not 0 <= ch < 16 for ch in muted | solo):
        raise MidiError('Invalid MIDI channel')
    return {(port, ch) for ch in range(16) if ch not in muted and (not solo or ch in solo)}


def sidecar_path(midi_path):
    return Path(str(midi_path) + '.xgw-routing.json')


def save_routing(midi_path, song, routes, default_port):
    validated = validate_routes(song, routes, default_port)
    data = {'version': 1, 'tracks': len(song.tracks), 'routes': [
        {'track': i, 'port': port, 'channel': channel}
        for i, (port, channel) in sorted(validated.items())]}
    target = sidecar_path(midi_path)
    temporary = target.with_name(target.name + '.tmp')
    try:
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def load_routing(midi_path, song, default_port):
    target = sidecar_path(midi_path)
    if not target.exists():
        return {}
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
        if type(data) is not dict or data.get('version') != 1 or data.get('tracks') != len(song.tracks):
            raise MidiError('Routing sidecar does not match this MIDI song')
        entries = data['routes']
        if type(entries) is not list:
            raise MidiError('Invalid routing entries')
        routes = {}
        for item in entries:
            i = item['track']
            if i in routes:
                raise MidiError('Duplicate routed track')
            routes[i] = (item['port'], item['channel'])
        return validate_routes(song, routes, default_port)
    except (ValueError, KeyError, TypeError, UnicodeError) as exc:
        raise MidiError(f'Invalid routing sidecar: {exc}') from exc
