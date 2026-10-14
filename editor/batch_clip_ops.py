"""Atomic batch operations on arrangement clips across MIDI tracks.

Clip indices refer to the arrangement before any edit. MIDI note pairs are
moved/copied together; non-note events can optionally follow clips; structural meta events stay put.
"""
from copy import deepcopy
from uuid import uuid4
from midi import MidiError
from clip_ops import edit_clip


def edit_clips(song, selections, delta, duplicate=False, destination_tracks=None, include_events=False):
    """Edit (track, clip) selections atomically, returning moved note count.

    destination_tracks maps source track indices to destination track indices.
    Multiple clips on the same track are supported; their indices are resolved
    from the original arrangement rather than recalculated after each edit.
    """
    if type(delta) is not int:
        raise MidiError('Tick offset must be an integer')
    if type(include_events) is not bool:
        raise MidiError('include_events must be a boolean')
    selections = list(selections)
    if not selections:
        raise MidiError('Select at least one clip')
    if len(set(selections)) != len(selections):
        raise MidiError('Duplicate clip selection')
    from arrangement import track_clips
    from note_ops import paired_notes
    from midi import Event
    destinations = destination_tracks or {}
    actions = []
    for track_index, clip_index in selections:
        if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
            raise MidiError('Invalid track')
        clips = track_clips(song.tracks[track_index], song.division)
        if type(clip_index) is not int or not 0 <= clip_index < len(clips):
            raise MidiError('Invalid clip')
        dest = destinations.get(track_index, track_index)
        if type(dest) is not int or not 0 <= dest < len(song.tracks):
            raise MidiError('Invalid destination track')
        start, end = clips[clip_index]
        events = []
        for on_idx, off_idx in paired_notes(song.tracks[track_index]):
            on = song.tracks[track_index].events[on_idx]
            if start <= on.tick < end:
                events.extend((song.tracks[track_index].events[on_idx], song.tracks[track_index].events[off_idx]))
        if include_events:
            # Clip intervals are half-open. Exclude all note messages (including
            # unpaired notes) and structural meta data such as tempo/signature.
            for event in song.tracks[track_index].events:
                if not start <= event.tick < end:
                    continue
                if 0x80 <= event.status <= 0x9f:
                    continue
                if event.status == 0xff:
                    continue
                events.append(event)
        if not events:
            raise MidiError('Clip has no complete notes')
        if any(not 0 <= e.tick + delta <= 0x0fffffff for e in events):
            raise MidiError('MIDI tick exceeds supported range')
        actions.append((track_index, dest, events))
    # A single MIDI event must never be edited twice by overlapping regions.
    # This can occur when manually authored region boundaries overlap note tails.
    touched = set()
    for source, _dest, events in actions:
        for event in events:
            key = (source, id(event))
            if key in touched:
                raise MidiError('Selected clips contain overlapping MIDI events')
            touched.add(key)
    # All validation precedes mutation. Build the final state on a copy.
    staged = deepcopy(song.tracks)
    count = 0
    for source, dest, events in actions:
        count += sum(1 for e in events if (e.status & 0xf0) == 0x90 and len(e.data) > 1 and e.data[1] > 0)
        target = staged[dest]
        if duplicate or source != dest:
            order = max((e.order for e in target.events), default=-1) + 1
            for e in events:
                target.events.append(Event(e.tick + delta, e.status, bytes(e.data), e.meta_type, order,
                                           uid=e.uid if not duplicate else uuid4().hex))
                order += 1
            if not duplicate:
                original = song.tracks[source].events
                indices = {id(e) for e in events}
                for index, event in enumerate(original):
                    if id(event) in indices:
                        staged[source].events[index] = None
        else:
            original = song.tracks[source].events
            indices = {id(e) for e in events}
            for index, event in enumerate(original):
                if id(event) in indices:
                    staged[source].events[index].tick += delta
    for track in staged:
        track.events = [e for e in track.events if e is not None]
    # Transfer explicit clip identities alongside MIDI data. Build region lists
    # from the pre-edit arrangement so selections retain their original indices.
    # If an interval conflicts with another, discard only that track's explicit
    # layout and fall back to the note-derived arrangement.
    affected = {source for source, _dest, _events in actions} | {dest for _source, dest, _events in actions}
    original_clips = {i: track_clips(song.tracks[i], song.division) for i in affected}
    selected_by_track = {}
    additions = {i: [] for i in affected}
    original_ids = {}
    for index in affected:
        ids = getattr(song.tracks[index], "clip_region_ids", None)
        original_ids[index] = (list(ids) if isinstance(ids, list) and len(ids) == len(original_clips[index])
                               else [uuid4().hex for _ in original_clips[index]])
    for source, clip_index in selections:
        selected_by_track.setdefault(source, set()).add(clip_index)
        dest = destinations.get(source, source)
        start, end = original_clips[source][clip_index]
        region_id = original_ids[source][clip_index]
        additions[dest].append(((start + delta, end + delta), uuid4().hex if duplicate else region_id))
    for index in affected:
        had_explicit = getattr(song.tracks[index], 'clip_regions', None) is not None
        # For ordinary non-explicit tracks, keep the normal inferred model.
        if not had_explicit and not any(
                getattr(song.tracks[source], 'clip_regions', None) is not None
                for source, clip_index in selections
                if destinations.get(source, source) == index):
            if hasattr(staged[index], 'clip_regions'):
                del staged[index].clip_regions
            if hasattr(staged[index], 'clip_region_ids'):
                del staged[index].clip_region_ids
            continue
        retained = []
        for clip_index, region in enumerate(original_clips[index]):
            selected = clip_index in selected_by_track.get(index, ())
            # Selected originals remain on a duplicate; otherwise they move.
            if not selected or duplicate:
                retained.append((region, original_ids[index][clip_index]))
        proposed = sorted(retained + additions[index], key=lambda item: item[0])
        intervals = [region for region, _uid in proposed]
        if (all(0 <= start < end <= 0x0fffffff for start, end in intervals)
                and all(left[1] <= right[0] for left, right in zip(intervals, intervals[1:]))):
            staged[index].clip_regions = intervals
            staged[index].clip_region_ids = [uid for _region, uid in proposed]
        else:
            if hasattr(staged[index], 'clip_regions'):
                del staged[index].clip_regions
            if hasattr(staged[index], 'clip_region_ids'):
                del staged[index].clip_region_ids
    song.tracks = staged
    song.dirty = True
    return count
