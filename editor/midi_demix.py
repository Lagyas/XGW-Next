"""Non-destructive SMF type-1 export with channel-separated musical tracks.

Channel voice events retain their original status/channel, tick, and ordering.
Global meta and SysEx events remain on a separate conductor/source track.
"""
from midi import Song, Track, Event, MidiError


def demix_to_format1(song):
    """Return an independent format-1 Song, splitting mixed MIDI tracks by channel.

    Each source track with channel events becomes one track per used channel.
    A single-channel source track stays intact. Non-channel events of a mixed
    source are kept on a separate track so no data are discarded.
    """
    if not isinstance(song, Song):
        raise TypeError('Expected a MIDI Song')
    if song.fmt == 2:
        raise MidiError('SMF type 2 contains independent sequences; cannot safely demix to type 1')
    tracks = []
    boundaries = []
    for source in song.tracks:
        boundaries.append(len(tracks))
        channels = sorted({event.status & 0x0f for event in source.events
                           if 0x80 <= event.status <= 0xef})
        if len(channels) <= 1:
            tracks.append(Track([Event(e.tick, e.status, bytes(e.data), e.meta_type, e.order)
                                 for e in source.events]))
            continue
        def clone(e):
            return Event(e.tick, e.status, bytes(e.data), e.meta_type, e.order)
        # Keep source metadata and conductor events together, with original timing.
        common = [e for e in source.events if not 0x80 <= e.status <= 0xef]
        if common:
            tracks.append(Track([clone(e) for e in common]))
        name = next((e.data for e in source.events
                     if e.status == 0xff and e.meta_type == 3), b'Track')
        for channel in channels:
            selected = [clone(e) for e in source.events if 0x80 <= e.status <= 0xef
                        and (e.status & 0x0f) == channel]
            # Give split tracks useful names without duplicating source meta events.
            selected.insert(0, Event(0, 0xff, name + b' [ch %d]' % (channel + 1), 3, -1))
            tracks.append(Track(selected))
    boundaries.append(len(tracks))
    # Non-MTrk chunks are legal SMF extensions. Keep each chunk at its
    # original source-track boundary even when that track was split.
    extras = [(boundaries[min(max(at, 0), len(song.tracks))],
               bytes(kind), bytes(payload))
              for at, kind, payload in song.extra_chunks]
    result = Song(1, song.division, tracks, header_extra=bytes(song.header_extra),
                  extra_chunks=extras)
    result.dirty = True
    return result
