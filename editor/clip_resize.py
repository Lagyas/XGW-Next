"""Safe right-edge resize of an arrangement MIDI part."""
from copy import deepcopy
from midi import MidiError
from arrangement import track_clips
from note_ops import paired_notes
from transport_ops import MAX_TICK


def resize_clip_right(song, track_index, clip_index, new_end):
    """Trim notes beyond a new right edge, or extend notes ending at old edge.

    Notes starting before the edge are retained; those entirely past the edge
    are removed. Other MIDI events are untouched. The change is atomic.
    """
    if not 0 < song.division < 0x8000 or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid MIDI track or division')
    track = song.tracks[track_index]
    clips = track_clips(track, song.division)
    if not 0 <= clip_index < len(clips):
        raise MidiError('Invalid MIDI part')
    start, end = clips[clip_index]
    if type(new_end) is not int or not start < new_end <= MAX_TICK:
        raise MidiError('Invalid MIDI part end')
    if new_end == end:
        return 0
    changes = []
    for a, b in paired_notes(track):
        on, off = track.events[a], track.events[b]
        if start <= on.tick < end:
            if new_end < end and on.tick >= new_end:
                changes.append((a, b, None))
            elif new_end < end and off.tick > new_end:
                changes.append((a, b, new_end))
            elif new_end > end and off.tick == end:
                changes.append((a, b, new_end))
    if not changes:
        return 0
    staged = deepcopy(track.events)
    deleted = set()
    for a, b, target in changes:
        if target is None:
            deleted.update((a, b))
        else:
            staged[b].tick = target
    track.events = [e for i, e in enumerate(staged) if i not in deleted]
    song.dirty = True
    return len(changes)
