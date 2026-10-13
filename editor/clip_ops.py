"""Move or duplicate complete note pairs belonging to an arrangement clip.

Only notes are edited; controllers, SysEx and tempo remain in place.
"""
from midi import Event, MidiError
from note_ops import paired_notes
from arrangement import track_clips

def edit_clip(song, track_index, clip_index, delta, duplicate=False, destination_track=None):
    if not isinstance(delta, int):
        raise MidiError("Tick offset must be an integer")
    if not 0 <= track_index < len(song.tracks):
        raise MidiError("Invalid track")
    if not 0 < song.division < 0x8000:
        raise MidiError("Only PPQN MIDI is supported")
    if destination_track is None:
        destination_track = track_index
    if not 0 <= destination_track < len(song.tracks):
        raise MidiError("Invalid destination track")
    track = song.tracks[track_index]
    clips = track_clips(track, song.division)
    if not 0 <= clip_index < len(clips):
        raise MidiError("Invalid clip")
    start, end = clips[clip_index]
    selected = []
    for on_idx, off_idx in paired_notes(track):
        on = track.events[on_idx]
        if start <= on.tick < end:
            selected.extend((track.events[on_idx], track.events[off_idx]))
    if not selected:
        raise MidiError("Clip has no complete notes")
    if min(e.tick for e in selected) + delta < 0:
        raise MidiError("Cannot move notes before tick zero")
    if max(e.tick for e in selected) + delta > 0x0fffffff:
        raise MidiError("MIDI tick exceeds supported range")
    destination = song.tracks[destination_track]
    if duplicate or destination_track != track_index:
        order = max((e.order for e in destination.events), default=0) + 1
        for e in selected:
            destination.events.append(Event(e.tick + delta, e.status, bytes(e.data),
                                      e.meta_type, order))
            order += 1
        if not duplicate:
            for e in selected:
                track.events.remove(e)
    else:
        for e in selected:
            e.tick += delta
    song.dirty = True
    return len(selected) // 2
