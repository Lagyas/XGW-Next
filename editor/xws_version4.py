"""Read-only validation of XGworks 4 trailer and S4WT channel evidence."""
from xws_import import _chunks, XGWORKS4_TRAILER
from midi import MidiError


def inspect_xws4(raw):
    chunks = list(_chunks(raw))
    trailer = chunks[-3:]
    present = any(kind in XGWORKS4_TRAILER for kind, _ in chunks)
    valid = (len(trailer) == 3 and
             tuple(kind for kind, _ in trailer) == XGWORKS4_TRAILER and
             all(body == bytes(4) for _, body in trailer) and
             not any(kind in XGWORKS4_TRAILER for kind, _ in chunks[:-3]))
    if present and not valid:
        raise MidiError('Invalid XGworks 4 trailer')
    tracks = sum(kind == b'S4WB' for kind, _ in chunks)
    metadata = [body for kind, body in chunks if kind == b'S4WT'][:tracks]
    channels = []
    for i, body in enumerate(metadata, 1):
        # Observed S4WT prefix byte 2 uses zero-based channel numbers.
        # Report only: never rewrite MIDI event channel status bytes.
        channels.append({'track': i, 'channel_candidate': body[2] + 1
                         if len(body) >= 33 and body[0] == 1 and body[2] < 16 else None})
    return {'xgworks4_trailer': valid, 'trailer_bytes': 36 if valid else 0,
            's4wt_channel_observations': channels}
