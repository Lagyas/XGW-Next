"""Opt-in, non-destructive Yamaha XG song export (XGX-9903R v2.01).

This is a conservative profile, not a compliance certificate. Existing channel
settings and effect SysEx take precedence over generated defaults.
"""
from midi import Song, Track, Event, MidiError
from midi_demix import demix_to_format1
from midi_compat import track_ports
from xg_effects import XGEffects, EFFECT_TYPE_ADDRESSES
from xg_sysex import decode_parameter_change

XG_SYSTEM_ON = bytes.fromhex('43 10 4c 00 00 7e 00 f7')
# Setup spacing is expressed in ticks at the target PPQN. Each entry is
# separated by at least one tick at PPQN 480, as Yamaha recommends.
PART_DEFAULTS = ((0, 0), (32, 0), (7, 100), (11, 127),
                 (91, 40), (93, 0), (94, 0))


def _copy(event, tick):
    return Event(tick, event.status, bytes(event.data), event.meta_type, event.order)


def _measure_ticks(song):
    """Use the time signature at song start; fall back to 4/4."""
    meter = (4, 2)
    for track in song.tracks:
        for event in track.events:
            if event.tick == 0 and event.status == 0xff and event.meta_type == 0x58 and len(event.data) >= 2:
                meter = event.data[0], event.data[1]
    numerator, denominator_power = meter
    if numerator == 0 or denominator_power > 7:
        raise MidiError('Invalid opening time signature for XG setup measure')
    duration = song.division * 4 * numerator
    if duration % (1 << denominator_power):
        raise MidiError('Setup measure is not an integer number of ticks')
    ticks = duration // (1 << denominator_power)
    if ticks < 64:
        raise MidiError('Opening measure is too short for safe XG setup')
    return ticks


def _initial_cc(event):
    return (event.tick == 0 and 0xb0 <= event.status <= 0xbf
            and len(event.data) == 2)


def _xg_effect_address(event):
    if event.status != 0xf0:
        return None
    decoded = decode_parameter_change(bytes((0xf0,)) + event.data)
    return decoded['address'] if decoded else None


def export_xg(song, level=2):
    """Create a fresh XG SMF with setup measure and ordered initial settings.

    All source notes and performance data are moved forward by one measure.
    Opening tempo/meter/key metadata remain at tick zero. Initial channel CC,
    bank selection, and program selection are placed in the setup measure.
    No existing user settings are overwritten; unsupported multiport routing
    is rejected rather than silently discarding port identity.
    """
    if not isinstance(song, Song):
        raise TypeError('Expected Song')
    if type(level) is not int or level not in (1, 2, 3):
        raise MidiError('XG level must be 1, 2 or 3')
    if song.fmt == 2 or song.division & 0x8000 or not 48 <= song.division <= 480:
        raise MidiError('XG export requires PPQN 48–480 and SMF format 0 or 1')
    setup_ticks = _measure_ticks(song)
    prepared = demix_to_format1(song)
    # MIDI port meta event 0x21 is meaningful for 32/64-part files. This
    # exporter has no port-aware channel mapping yet, so do not collapse it.
    port_values = {port for port in track_ports(prepared) if port is not None}
    if len(port_values) > 1 or (port_values and port_values != {0}):
        raise MidiError('Multiport XG export requires explicit port mapping')
    channels = {e.status & 15 for t in prepared.tracks for e in t.events
                if 0x80 <= e.status <= 0xef}
    if len(channels) > {1: 16, 2: 32, 3: 64}[level]:
        raise MidiError('Too many parts for selected XG level')

    tracks = []
    system_on = False
    effect_addresses = set(EFFECT_TYPE_ADDRESSES.values())
    existing_effects = set()
    for source in prepared.tracks:
        for e in source.events:
            if e.tick == 0 and _xg_effect_address(e) in effect_addresses:
                existing_effects.add(_xg_effect_address(e))
    for source in prepared.tracks:
        source_channels = {e.status & 15 for e in source.events if 0x80 <= e.status <= 0xef}
        if len(source_channels) > 1:
            raise MidiError('XG Format 1 part track contains multiple channels')
        channel = next(iter(source_channels)) if source_channels else None
        events = []
        initial = [e for e in source.events if _initial_cc(e)
                   and channel is not None and (e.status & 15) == channel]
        initial_programs = [e for e in source.events if e.tick == 0 and channel is not None
                            and e.status == (0xc0 | channel)]
        # The last value of each initial controller wins; avoids duplicate CC
        # at the same step and preserves user-defined settings.
        initial_values = {e.data[0]: e.data[1] for e in initial}
        for e in source.events:
            if e.status == 0xff and e.meta_type == 0x2f:
                continue
            if e in initial or e in initial_programs:
                continue
            global_zero = (e.tick == 0 and e.status == 0xff
                           and e.meta_type in (0x02, 0x03, 0x51, 0x58, 0x59))
            initial_sysex = e.tick == 0 and e.status in (0xf0, 0xf7)
            if e.status == 0xf0 and e.data == XG_SYSTEM_ON and e.tick == 0:
                system_on = True
            events.append(_copy(e, 0 if global_zero or initial_sysex else e.tick + setup_ticks))
        if channel is not None:
            status = 0xb0 | channel
            # CC0, CC32, Program Change and the remaining controllers are
            # separated by a tick, preserving the Yamaha-required order.
            sequence = [(cc, initial_values.get(cc, default)) for cc, default in PART_DEFAULTS[:2]]
            sequence += [('program', initial_programs[-1].data[0])] if initial_programs else []
            sequence += [(cc, initial_values.get(cc, default)) for cc, default in PART_DEFAULTS[2:]]
            sequence += [(cc, val) for cc, val in initial_values.items()
                         if cc not in {item[0] for item in PART_DEFAULTS}]
            for offset, (cc, value) in enumerate(sequence, start=12):
                if offset >= setup_ticks:
                    raise MidiError('Not enough room in opening measure for XG part setup')
                if cc == 'program':
                    events.append(Event(offset, 0xc0 | channel, bytes((value,)), order=-80))
                else:
                    events.append(Event(offset, status, bytes((cc, value)), order=-80))
        tracks.append(Track(events))
    if not tracks:
        tracks = [Track([])]
    # Yamaha places effect SysEx in the channel-1 part track when available.
    ch1_track = next((t for t in tracks if any(0x80 <= e.status <= 0xef
                       and (e.status & 15) == 0 for e in t.events)), tracks[0])
    if not system_on:
        ch1_track.events.append(Event(0, 0xf0, XG_SYSTEM_ON, order=-200))
    effects = XGEffects()
    for offset, effect in enumerate(('reverb', 'chorus', 'variation'), start=2):
        if EFFECT_TYPE_ADDRESSES[effect] not in existing_effects:
            ch1_track.events.append(Event(offset, 0xf0, effects.message(effect)[1:], order=-190))
    if level == 1:
        merged = [e for t in tracks for e in t.events]
        names = [e for e in merged if e.status == 0xff and e.meta_type == 3]
        merged = [e for e in merged if not (e.status == 0xff and e.meta_type == 3)]
        if names:
            merged.append(names[0])
        tracks = [Track(merged)]
    result = Song(0 if level == 1 else 1, song.division, tracks)
    result.dirty = True
    return result
