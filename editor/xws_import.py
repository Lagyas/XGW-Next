"""Conservative XGworks 4 S4WB -> SMF MIDI conversion.

S4WB uses SMF-like delta times, but positive-velocity note-ons carry a
four-byte big-endian duration instead of a separate note-off event.
This importer intentionally does not claim to restore XWS mixer/clip metadata.
"""
from pathlib import Path
from midi import Event, Track, Song, MidiError, vlq_read, decode_text

MAX_FILE = 32 * 1024 * 1024
MAX_EVENTS = 1_000_000
XGWORKS4_TRAILER = (b'SCRS', b'SCRA', b'SCRD')


def _chunks(raw):
    if len(raw) < 72 or raw[:4] != b'S4WH':
        raise MidiError('Not a supported S4WH XGworks project')
    pos = 0
    while pos < len(raw):
        if pos + 8 > len(raw):
            raise MidiError('Truncated XWS chunk header')
        kind = raw[pos:pos + 4]
        size = int.from_bytes(raw[pos + 4:pos + 8], 'big')
        end = pos + 8 + size
        if end > len(raw):
            raise MidiError('Truncated XWS chunk body')
        yield kind, raw[pos + 8:end]
        pos = end


def _decode_track(data):
    pos = tick = 0
    running = None
    events = []
    generated_off_ids = set()
    while pos < len(data):
        if len(events) > MAX_EVENTS:
            raise MidiError('Too many XWS events')
        delta, pos = vlq_read(data, pos, len(data))
        tick += delta
        if tick > 0x0fffffff:
            raise MidiError('XWS tick exceeds MIDI range')
        if pos >= len(data):
            raise MidiError('Truncated XWS event')
        status = data[pos]
        if status & 0x80:
            pos += 1
            running = status if status < 0xf0 else None
        else:
            if running is None:
                raise MidiError('Invalid XWS running status')
            status = running
        meta = -1
        if status == 0xff:
            if pos >= len(data):
                raise MidiError('Truncated XWS meta event')
            meta = data[pos]
            pos += 1
            size, pos = vlq_read(data, pos, len(data))
        elif status in (0xf0, 0xf7):
            size, pos = vlq_read(data, pos, len(data))
        elif 0x80 <= status <= 0xef:
            size = 1 if status & 0xf0 in (0xc0, 0xd0) else 2
        else:
            raise MidiError(f'Unsupported XWS event status {status:02x}')
        if pos + size > len(data):
            raise MidiError('Truncated XWS event payload')
        payload = data[pos:pos + size]
        pos += size
        if status < 0xf0 and any(byte >= 128 for byte in payload):
            raise MidiError('Invalid XWS MIDI data byte')
        events.append(Event(tick, status, payload, meta, len(events)))
        if status & 0xf0 == 0x90 and payload[1] != 0:
            if pos + 4 > len(data):
                raise MidiError('Truncated XWS note duration')
            duration = int.from_bytes(data[pos:pos + 4], 'big')
            pos += 4
            if duration and tick + duration > 0x0fffffff:
                raise MidiError('XWS note exceeds MIDI tick range')
            # The four-byte duration belongs to the note-on, not the delta stream.
            off = Event(tick + duration, 0x80 | (status & 15), bytes((payload[0], 0)), order=len(events))
            events.append(off)
            if duration:
                generated_off_ids.add(off.uid)
    # End a previous note before re-triggering the same pitch at its end.
    # Keep zero-length note-on/off pairs in their original order.
    events.sort(key=lambda e: (e.tick, 0 if e.uid in generated_off_ids else 1, e.order))
    for order, event in enumerate(events):
        event.order = order
    return Track(events)


def _track_name(body):
    """Extract the first S4WT track label; ignore unrecognized metadata layouts."""
    if len(body) < 34 or body[0] != 1:
        return None
    length = body[32]
    if not 1 <= length <= 127 or 33 + length > len(body):
        return None
    name = body[33:33 + length]
    if any(byte < 32 or byte == 127 for byte in name):
        return None
    return name


def import_xws_bytes(raw):
    if len(raw) > MAX_FILE:
        raise MidiError('XWS file exceeds safe import limit')
    tracks = []
    header = None
    names = []
    trailer_index = 0
    for kind, body in _chunks(raw):
        if kind in XGWORKS4_TRAILER:
            if kind != XGWORKS4_TRAILER[trailer_index] or len(body) != 4 or body != bytes(4):
                raise MidiError('Invalid XGworks 4 trailer')
            trailer_index += 1
            continue
        if trailer_index:
            raise MidiError('XGworks 4 trailer must be final')
        if kind == b'S4WH':
            if header is not None:
                raise MidiError('Duplicate XWS header')
            header = body
        elif kind == b'S4WB':
            tracks.append(_decode_track(body))
        elif kind == b'S4WT':
            # The first group of S4WT records is aligned to the S4WB
            # sequence tracks, including unnamed entries. Subsequent S4WT
            # groups describe other objects; do not shift track names by
            # filtering out blank labels or consuming later groups.
            if len(names) < len(tracks):
                names.append(_track_name(body))
        elif kind != b'S4ST':
            raise MidiError(f'Unknown XWS chunk {kind!r}')
    if trailer_index not in (0, 3):
        raise MidiError('Incomplete XGworks 4 trailer')
    if not tracks:
        raise MidiError('XWS has no sequence tracks')
    # XGworks header stores PPQN as big-endian uint16 at file offset 16.
    division = int.from_bytes(header[8:10], 'big')
    if not 1 <= division <= 0x7fff:
        raise MidiError('Invalid XWS MIDI timebase')
    for index, name in enumerate(names):
        if name is None:
            continue
        track = tracks[index]
        track.events.insert(0, Event(0, 0xff, name, 3, 0))
        for order, event in enumerate(track.events):
            event.order = order
    song = Song(1, division, tracks)
    song.dirty = True
    # Validate that every converted track can be serialized and read as SMF.
    Song.from_bytes(song.to_bytes())
    return song


def import_xws(path):
    return import_xws_bytes(Path(path).read_bytes())


def track_setup_report(song):
    """Report only MIDI settings actually present in decoded events.

    This is not an interpretation of undocumented S4WT mixer bytes. Values
    describe the last event seen in each channel, not the original GUI state.
    """
    result = []
    for index, track in enumerate(song.tracks, 1):
        channels = {}
        sysex = 0
        for event in sorted(track.events, key=lambda e: (e.tick, e.order)):
            status = event.status
            if status in (0xf0, 0xf7):
                sysex += 1
            if not 0x80 <= status <= 0xef:
                continue
            channel = (status & 15) + 1
            state = channels.setdefault(channel, {})
            high = status & 0xf0
            if high == 0xc0:
                state['program'] = event.data[0] + 1  # UI numbering
            elif high == 0xb0:
                control, value = event.data
                field = {0: 'bank_msb', 32: 'bank_lsb', 7: 'volume',
                         10: 'pan', 11: 'expression', 91: 'reverb',
                         93: 'chorus'}.get(control)
                if field:
                    state[field] = value
        result.append({'track': index, 'name': track.name(),
                       'channels': channels, 'sysex_events': sysex})
    return result


def format_track_setup_report(song):
    """Human-readable, evidence-based XWS MIDI setup audit."""
    lines = ['XWS MIDI event setup (last observed values, not XGworks mixer state)',
             f'Tracks: {len(song.tracks)}']
    for track in track_setup_report(song):
        lines.append(f"Track {track['track']}: {track['name']}")
        if not track['channels']:
            lines.append('  No channel MIDI events')
        for channel, settings in sorted(track['channels'].items()):
            fields = ', '.join(f'{key}={value}' for key, value in sorted(settings.items()))
            lines.append(f'  Channel {channel}' + (f': {fields}' if fields else ': no setup events'))
        if track['sysex_events']:
            lines.append(f"  SysEx events: {track['sysex_events']} (preserved, not interpreted)")
    return '\n'.join(lines)


def inspect_s4wt_records(raw):
    """Return read-only, positionally aligned S4WT observations.

    Offsets 1, 2, 7-11 are deliberately raw bytes, NOT interpreted as
    mixer/channel settings. Other S4WT groups are not sequence tracks.
    """
    if len(raw) > MAX_FILE:
        raise MidiError('XWS file exceeds safe import limit')
    track_count = 0
    records = []
    for kind, body in _chunks(raw):
        if kind == b'S4WB':
            track_count += 1
        elif kind == b'S4WT':
            index = len(records)
            if len(body) < 33:
                raise MidiError('Truncated S4WT metadata record')
            name = _track_name(body) if index < track_count else None
            records.append({
                'record': index + 1,
                'sequence_track': index + 1 if index < track_count else None,
                'length': len(body),
                'name': name.decode('ascii') if name is not None and name.isascii() else
                        (decode_text(name) if name is not None else None),
                'raw_prefix': body[:12].hex(' '),
                'raw_tail_length': len(body) - 33 - (body[32] if index < track_count and name is not None else 0),
            })
    return records


def format_s4wt_report(raw):
    records = inspect_s4wt_records(raw)
    aligned = [record for record in records if record['sequence_track'] is not None]
    lines = ['XGworks S4WT metadata audit (read-only; raw bytes are NOT mixer settings)',
             f'S4WT records: {len(records)}; sequence-aligned records: {len(aligned)}',
             'Columns: record, MIDI track, bytes, name, first 12 raw bytes']
    for record in records:
        if record['sequence_track'] is None:
            continue
        lines.append(f"{record['record']:3d} | {record['sequence_track']:3d} | "
                     f"{record['length']:4d} | {record['name'] or '(unnamed)'} | "
                     f"{record['raw_prefix']}")
    lines.append(f'Additional S4WT records not assigned to sequence tracks: {len(records) - len(aligned)}')
    lines.append('No volume, pan, bank or channel is inferred from undocumented S4WT offsets.')
    return '\n'.join(lines)


def compare_s4wt_records(before, after):
    """Compare positionally aligned S4WT track records without assigning semantics.

    The variable-length name field (offset 32 onward) is excluded: differences
    in it cannot be treated as evidence of mixer settings. Returns byte offsets
    only for the fixed 32-byte prefix, plus length/name changes separately.
    """
    def extract(raw):
        if len(raw) > MAX_FILE:
            raise MidiError('XWS file exceeds safe import limit')
        track_count = 0
        bodies = []
        for kind, body in _chunks(raw):
            if kind == b'S4WB':
                track_count += 1
            elif kind == b'S4WT':
                bodies.append(body)
        if not track_count or len(bodies) < track_count:
            raise MidiError('XWS lacks aligned S4WT track records')
        if any(len(b) < 33 for b in bodies[:track_count]):
            raise MidiError('Truncated S4WT metadata record')
        return bodies[:track_count]

    a, b = extract(before), extract(after)
    if len(a) != len(b):
        raise MidiError('XWS projects have different MIDI track counts')
    changes = []
    for index, (old, new) in enumerate(zip(a, b), 1):
        changed = [(offset, old[offset], new[offset]) for offset in range(32)
                   if old[offset] != new[offset]]
        old_name, new_name = _track_name(old), _track_name(new)
        if changed or old_name != new_name or len(old) != len(new) or old[32:] != new[32:]:
            changes.append({'track': index, 'fixed_prefix_changes': changed,
                            'name_before': old_name, 'name_after': new_name,
                            'length_before': len(old), 'length_after': len(new),
                            'variable_tail_changed': old[32:] != new[32:]})
    return changes


def format_s4wt_comparison(before, after):
    changes = compare_s4wt_records(before, after)
    lines = ['XGworks S4WT comparison (read-only; byte offsets are NOT decoded settings)',
             f'Changed sequence track records: {len(changes)}']
    for row in changes:
        lines.append(f"Track {row['track']}: {row['length_before']} -> {row['length_after']} bytes")
        if row['name_before'] != row['name_after']:
            lines.append(f"  Name changed: {row['name_before']!r} -> {row['name_after']!r}")
        for offset, old, new in row['fixed_prefix_changes']:
            lines.append(f'  Fixed offset {offset:02d}: {old:02X} -> {new:02X}')
        if row['variable_tail_changed']:
            lines.append('  Variable name/tail region changed (not interpreted)')
    lines.append('Compare files differing in ONE known XGworks setting to identify candidate offsets.')
    lines.append('No channel, volume, pan or bank is inferred from these byte differences.')
    return '\n'.join(lines)
