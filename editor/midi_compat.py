"""Read-only MIDI interchange inspection; never rewrites source events."""
from midi import Song, MidiError

GM_ON = bytes.fromhex('7e 7f 09 01 f7')
GM2_ON = bytes.fromhex('7e 7f 09 03 f7')
XG_ON = bytes.fromhex('43 10 4c 00 00 7e 00 f7')


def sysex_profiles(song):
    """Identify explicit reset messages; absence is not proof of incompatibility."""
    if not isinstance(song, Song):
        raise TypeError('Expected Song')
    found = set()
    for track in song.tracks:
        for event in track.events:
            if event.status != 0xf0:
                continue
            data = event.data
            if len(data) == 5 and data[0] == 0x7e and data[2:] == b'\x09\x01\xf7' and data[1] <= 0x7f:
                found.add('GM')
            if len(data) == 5 and data[0] == 0x7e and data[2:] == b'\x09\x03\xf7' and data[1] <= 0x7f:
                found.add('GM2')
            if len(data) == 8 and data[0] == 0x43 and 0x10 <= data[1] <= 0x1f and data[2:] == XG_ON[2:]:
                found.add('XG')
            # GS Reset: Roland DT1, model 42, address 40 00 7F, data 00.
            if (len(data) >= 10 and data[0] == 0x41 and data[2:4] == b'\x42\x12'
                    and data[4:8] == b'\x40\x00\x7f\x00' and data[-1] == 0xf7):
                checksum = (-sum(data[4:8])) & 0x7f
                if data[8] == checksum:
                    found.add('GS')
    return found


def track_ports(song):
    """Track-level SMF MIDI Port (FF 21 01 pp) observations, or None.

    Reject conflicting port changes within one track: the application routes
    at track granularity and cannot safely represent such a stream.
    """
    if not isinstance(song, Song):
        raise TypeError('Expected Song')
    result = []
    for index, track in enumerate(song.tracks):
        values = {e.data[0] for e in track.events
                  if e.status == 0xff and e.meta_type == 0x21 and len(e.data) == 1}
        malformed = any(e.status == 0xff and e.meta_type == 0x21 and len(e.data) != 1
                        for e in track.events)
        if malformed or len(values) > 1:
            raise MidiError(f'Ambiguous MIDI port metadata on track {index + 1}')
        result.append(next(iter(values)) if values else None)
    return tuple(result)


def audit_roundtrip(song):
    """Validate edited SMF serialization retains all meaningful MIDI events.

    EOT events are synthesized/repositioned by the SMF writer and are excluded.
    """
    if not isinstance(song, Song):
        raise TypeError('Expected Song')
    def signature(source):
        # Ordering at the same tick matters: bank select must precede program
        # change, and note-off/note-on order can change playback behavior.
        return [[(e.tick, e.status, e.meta_type, e.data)
                 for e in sorted(track.events, key=lambda event: (event.tick, event.order))
                 if not (e.status == 0xff and e.meta_type == 0x2f)]
                for track in source.tracks]
    clone = Song.from_bytes(song.to_bytes())
    if song.fmt != clone.fmt or song.division != clone.division or signature(song) != signature(clone):
        raise MidiError('MIDI round-trip changed musical events')
    if song.extra_chunks != clone.extra_chunks:
        raise MidiError('MIDI round-trip changed nonstandard chunks')
    return True
