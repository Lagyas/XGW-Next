"""Demix MIDI note events into independent tracks by channel and pitch."""
from midi import Song, Track, Event, MidiError

DRUM_NAMES = {
 35:'Acoustic Bass Drum',36:'Bass Drum 1',37:'Side Stick',38:'Acoustic Snare',
 39:'Hand Clap',40:'Electric Snare',41:'Low Floor Tom',42:'Closed Hi-Hat',
 43:'High Floor Tom',44:'Pedal Hi-Hat',45:'Low Tom',46:'Open Hi-Hat',
 47:'Low-Mid Tom',48:'Hi-Mid Tom',49:'Crash Cymbal 1',50:'High Tom',
 51:'Ride Cymbal 1',52:'Chinese Cymbal',53:'Ride Bell',54:'Tambourine',
 55:'Splash Cymbal',56:'Cowbell',57:'Crash Cymbal 2',58:'Vibraslap',
 59:'Ride Cymbal 2',60:'Hi Bongo',61:'Low Bongo',62:'Mute Hi Conga',
 63:'Open Hi Conga',64:'Low Conga',65:'High Timbale',66:'Low Timbale',
 67:'High Agogo',68:'Low Agogo',69:'Cabasa',70:'Maracas',71:'Short Whistle',
 72:'Long Whistle',73:'Short Guiro',74:'Long Guiro',75:'Claves',
 76:'Hi Wood Block',77:'Low Wood Block',78:'Mute Cuica',79:'Open Cuica',
 80:'Mute Triangle',81:'Open Triangle'
}

def demix_drums_by_note(song, channels=range(16)):
    if not isinstance(song, Song):
        raise TypeError('Expected Song')
    if song.fmt == 2:
        raise MidiError('SMF format 2 cannot be safely converted to format 1')
    channels = set(channels)
    if not channels or any(type(c) is not int or not 0 <= c <= 15 for c in channels):
        raise ValueError('Invalid MIDI channels')
    tracks, boundaries, created = [], [], 0
    def clone(e):
        return Event(e.tick, e.status, bytes(e.data), e.meta_type, e.order)
    def is_note(e):
        return (0x80 <= e.status <= 0xef and (e.status & 15) in channels
                and (e.status & 0xf0) in (0x80, 0x90, 0xa0) and bool(e.data))
    for source in song.tracks:
        boundaries.append(len(tracks))
        keys = sorted({(e.status & 15, e.data[0]) for e in source.events if is_note(e)})
        if not keys:
            tracks.append(Track([clone(e) for e in source.events]))
            continue
        remaining = [clone(e) for e in source.events if not is_note(e)]
        if remaining:
            tracks.append(Track(remaining))
        for ch, pitch in keys:
            notes = [clone(e) for e in source.events
                     if is_note(e) and (e.status & 15, e.data[0]) == (ch, pitch)]
            label = (f'CH {ch+1} - {DRUM_NAMES[pitch]} ({pitch})'
                     if ch in (9, 10) and pitch in DRUM_NAMES
                     else f'CH {ch+1} - Note {pitch}')
            notes.insert(0, Event(0, 0xff, label.encode('ascii'), 3, -1))
            tracks.append(Track(notes))
            created += 1
    boundaries.append(len(tracks))
    extras = [(boundaries[min(max(at, 0), len(song.tracks))], bytes(kind), bytes(payload))
              for at, kind, payload in song.extra_chunks]
    result = Song(1, song.division, tracks, header_extra=bytes(song.header_extra),
                  extra_chunks=extras)
    result.dirty = True
    return result, created
