"""Non-destructive validation and atomic note-aware clip boundary edits.

Arrangement clips are inferred from notes, not stored as regions. Splitting a
sustained note produces two contiguous notes; a split in silence is not
representable as two clips without adding a persistent region model.
"""
from copy import deepcopy
from midi import Event, MidiError
from arrangement import track_clips
from note_ops import paired_notes

MAX_TICK = 0x0fffffff

def _clip(song, track_index, clip_index):
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track')
    if not 0 < song.division < 0x8000:
        raise MidiError('PPQN timing required')
    clips = track_clips(song.tracks[track_index], song.division)
    if type(clip_index) is not int or not 0 <= clip_index < len(clips):
        raise MidiError('Invalid clip')
    return clips[clip_index]

def split_sustained_notes(song, track_index, clip_index, tick):
    """Split notes crossing tick, preserving channel, pitch and velocity.

    This edits note boundaries, not arrangement region boundaries. If no note
    crosses the cut, no change is made.
    """
    start, end = _clip(song, track_index, clip_index)
    if type(tick) is not int or not start < tick < end:
        raise MidiError('Split must lie strictly inside the clip')
    track = song.tracks[track_index]
    pairs = [(track.events[a], track.events[b]) for a,b in paired_notes(track)
             if start <= track.events[a].tick < tick < track.events[b].tick]
    if not pairs:
        return 0
    staged = deepcopy(track.events)
    order = max((e.order for e in staged), default=-1) + 1
    for on, off in pairs:
        on_idx = next(i for i,e in enumerate(track.events) if e is on)
        off_idx = next(i for i,e in enumerate(track.events) if e is off)
        staged[off_idx].tick = tick
        staged.extend((Event(tick, on.status, bytes(on.data), order=order),
                       Event(off.tick, off.status, bytes(off.data), order=order+1)))
        order += 2
    track.events = staged
    song.dirty = True
    return len(pairs)

def trim_clip_notes(song, track_index, clip_index, left, right):
    """Crop matched notes to [left,right); delete fully outside notes in clip.

    Non-note MIDI events, tempo and SysEx are left unchanged. Clip endpoints
    must be within the original clip; operations are atomic.
    """
    start, end = _clip(song, track_index, clip_index)
    if any(type(v) is not int for v in (left,right)) or not start <= left < right <= end:
        raise MidiError('Invalid crop boundaries')
    track = song.tracks[track_index]
    changes = []
    for a,b in paired_notes(track):
        on, off = track.events[a], track.events[b]
        if start <= on.tick < end:
            if off.tick <= left or on.tick >= right:
                changes.append((a,b,None,None))
            else:
                changes.append((a,b,max(left,on.tick),min(right,off.tick)))
    if not changes:
        return 0
    staged = deepcopy(track.events)
    delete = set()
    changed = 0
    for a,b,new_start,new_end in changes:
        if new_start is None or new_start >= new_end:
            delete.update((a,b)); changed += 1
        elif staged[a].tick != new_start or staged[b].tick != new_end:
            staged[a].tick, staged[b].tick = new_start,new_end
            changed += 1
    if changed:
        track.events = [e for i,e in enumerate(staged) if i not in delete]
        song.dirty = True
    return changed

def legato_clip_notes(song, track_index, clip_index, gap=0, same_pitch=False):
    """Extend each note to the next onset in its channel (optionally pitch).

    Never shorten existing notes or cross a following note-on of the same pitch;
    preserve non-note events. This is a note-level operation, not clip merging.
    """
    start, end = _clip(song, track_index, clip_index)
    if type(gap) is not int or gap < 0 or type(same_pitch) is not bool:
        raise MidiError('Invalid legato settings')
    track = song.tracks[track_index]
    pairs = paired_notes(track)
    notes = [(a, b, track.events[a], track.events[b]) for a, b in pairs
             if start <= track.events[a].tick < end]
    changes = []
    for a, b, on, off in notes:
        channel = on.status & 15
        following = [other_on.tick for _, _, other_on, _ in notes
                     if (other_on.status & 15) == channel
                     and (not same_pitch or other_on.data[0] == on.data[0])
                     and other_on.tick > on.tick]
        if not following:
            continue
        target = min(following) - gap
        if target > off.tick and target <= MAX_TICK:
            changes.append((b, target))
    if changes:
        staged = deepcopy(track.events)
        for index, target in changes:
            staged[index].tick = target
        track.events = staged
        song.dirty = True
    return len(changes)
