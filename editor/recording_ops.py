"""Non-destructive MIDI recording placement and overdub operations."""
from midi import Event, MidiError, Track


def merge_take(target, take):
    """Overlay captured channel events onto a track without altering existing events.

    Preserve all meta/SysEx events and their relative order; insert recorded events
    after existing events at the same tick. Returns a new Track for undo safety.
    """
    if not isinstance(target, Track) or not isinstance(take, Track):
        raise MidiError('Overdub requires MIDI tracks')
    existing = [Event(e.tick, e.status, e.data, e.meta_type, e.order, e.uid)
                for e in target.events]
    for e in take.events:
        if not (0x80 <= e.status <= 0xef):
            raise MidiError('Overdub take must contain only MIDI channel events')
        if type(e.tick) is not int or not 0 <= e.tick <= 0x0fffffff:
            raise MidiError('Invalid recorded MIDI tick')
    all_ids = [e.uid for e in target.events] + [e.uid for e in take.events]
    if len(all_ids) != len(set(all_ids)):
        raise MidiError('Duplicate MIDI event identity in overdub')
    # Existing EOT remains in the track and is moved to the final tick by SMF writer.
    ordered = sorted(enumerate(existing), key=lambda row: (row[1].tick, row[1].order, row[0]))
    result = []
    index = 0
    captured = sorted(enumerate(take.events), key=lambda row: (row[1].tick, row[0]))
    for _, event in captured:
        while index < len(ordered) and ordered[index][1].tick <= event.tick:
            result.append(ordered[index][1])
            index += 1
        result.append(Event(event.tick, event.status, event.data, event.meta_type, 0, event.uid))
    result.extend(event for _, event in ordered[index:])
    for order, event in enumerate(result):
        event.order = order
    return Track(result)


def quantize_take_onsets(take, grid, origin=0, strength=100):
    """Snap recorded note starts to a tick grid without shortening their duration.

    Note-off pairs follow their matching note-on by the same displacement.
    Controllers, unpaired note-offs and the original take remain unchanged.
    """
    if not isinstance(take, Track):
        raise MidiError('Quantization requires a MIDI track')
    if (type(grid) is not int or grid < 0 or grid > 0x0fffffff
            or type(origin) is not int or not 0 <= origin <= 0x0fffffff):
        raise MidiError('Invalid recording quantization grid')
    result = [Event(e.tick, e.status, e.data, e.meta_type, e.order, e.uid)
              for e in take.events]
    if type(strength) is not int or not 0 <= strength <= 100:
        raise MidiError("Quantization strength must be 0–100 percent")
    if not grid or strength == 0:
        return Track(result)
    active = {}
    for i, event in sorted(enumerate(result), key=lambda row: (row[1].tick, row[1].order, row[0])):
        kind = event.status & 0xf0
        if not (0x80 <= event.status <= 0xef and kind in (0x80, 0x90)
                and len(event.data) == 2):
            continue
        key = (event.status & 15, event.data[0])
        if kind == 0x90 and event.data[1] > 0:
            delta = event.tick - origin
            # Halfway values round forward; never quantize before tick zero.
            snapped = max(0, origin + ((delta * 2 + grid) // (2 * grid)) * grid)
            snapped = min(snapped, 0x0fffffff)
            full_shift = snapped - event.tick
            displacement = (abs(full_shift) * strength + 50) // 100
            if full_shift < 0:
                displacement = -displacement
            active.setdefault(key, []).append(displacement)
            event.tick = max(0, min(0x0fffffff, event.tick + displacement))
        elif active.get(key):
            displacement = active[key].pop(0)
            event.tick = max(0, min(0x0fffffff, event.tick + displacement))
            if not active[key]:
                del active[key]
    result.sort(key=lambda e: (e.tick, e.order))
    for i, event in enumerate(result):
        event.order = i
    return Track(result)


def replace_take_range(target, take, start, end, *, channels=None):
    """Replace channel events in [start, end) while preserving meta/SysEx.

    A punch take may contain notes extending outside the region; the caller
    must provide already-clipped recorded events. The source tracks are never
    mutated, and invalid inputs fail before any edits.
    """
    if not isinstance(target, Track) or not isinstance(take, Track):
        raise MidiError('Punch replacement requires MIDI tracks')
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= 0x0fffffff:
        raise MidiError('Invalid punch range')
    if channels is not None:
        if not isinstance(channels, (set, frozenset, list, tuple)) or any(type(ch) is not int or not 0 <= ch < 16 for ch in channels):
            raise MidiError('Invalid punch channels')
        channels = set(channels)
    for event in take.events:
        if not (0x80 <= event.status <= 0xef) or not start <= event.tick < end:
            raise MidiError('Recorded event outside punch region or not channel MIDI')
    retained = [event for event in target.events if not (
        0x80 <= event.status <= 0xef and start <= event.tick < end
        and (channels is None or (event.status & 15) in channels))]
    all_ids = [e.uid for e in retained] + [e.uid for e in take.events]
    if len(all_ids) != len(set(all_ids)):
        raise MidiError('Duplicate MIDI event identity in punch replacement')
    events = [Event(e.tick, e.status, e.data, e.meta_type, e.order, e.uid) for e in retained]
    events.extend(Event(e.tick, e.status, e.data, e.meta_type, e.order, e.uid) for e in take.events)
    events.sort(key=lambda e: (e.tick, e.order))
    for i, event in enumerate(events):
        event.order = i
    return Track(events)


def replace_take_range_sustain_safe(target, take, start, end, *, channels=None):
    """Punch replace with boundary-aware note pairing.

    Notes sounding across the punch-in/out boundary are shortened or resumed
    so removal of note messages inside the punch cannot leave stuck notes.
    Newly recorded note messages must already be within the punch interval.
    """
    if not isinstance(target, Track) or not isinstance(take, Track):
        raise MidiError('Punch replacement requires MIDI tracks')
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= 0x0fffffff:
        raise MidiError('Invalid punch range')
    if channels is not None:
        if not isinstance(channels, (set, frozenset, list, tuple)) or any(type(ch) is not int or not 0 <= ch < 16 for ch in channels):
            raise MidiError('Invalid punch channels')
        channels = set(channels)
    for event in take.events:
        if not (0x80 <= event.status <= 0xef) or not start <= event.tick < end:
            raise MidiError('Recorded event outside punch region or not channel MIDI')
        if channels is not None and (event.status & 15) not in channels:
            raise MidiError('Recorded event channel outside punch selection')
    # Pair original note messages chronologically. Unpaired note messages are
    # left to the ordinary replacement operation.
    ordered = sorted(enumerate(target.events), key=lambda p: (p[1].tick, p[1].order, p[0]))
    active = {}
    pairs = []
    for _, e in ordered:
        if not 0x80 <= e.status <= 0x9f or len(e.data) < 2:
            continue
        key = (e.status & 15, e.data[0])
        if (e.status & 0xf0) == 0x90 and e.data[1] != 0:
            active.setdefault(key, []).append(e)
        elif active.get(key):
            on = active[key].pop(0)
            pairs.append((on, e))
    # Build a new track without modifying the source. Remove all note messages
    # belonging to affected pairs and reconstruct only their outside portions.
    affected = set()
    additions = []
    for on, off in pairs:
        channel = on.status & 15
        if channels is not None and channel not in channels:
            continue
        if on.tick >= end or off.tick <= start:
            continue
        affected.update((on.uid, off.uid))
        if on.tick < start:
            additions.extend((Event(on.tick, on.status, on.data, order=on.order, uid=on.uid),
                              Event(start, 0x80 | channel, bytes((on.data[0], 0)))))
        if off.tick > end:
            additions.extend((Event(end, on.status, on.data),
                              Event(off.tick, off.status, off.data, order=off.order, uid=off.uid)))
    remaining = Track([Event(e.tick, e.status, e.data, e.meta_type, e.order, e.uid)
                       for e in target.events if e.uid not in affected])
    replaced = replace_take_range(remaining, take, start, end, channels=channels)
    ids = {e.uid for e in replaced.events}
    if any(e.uid in ids for e in additions):
        raise MidiError('Duplicate MIDI event identity in punch boundary reconstruction')
    replaced.events.extend(additions)
    replaced.events.sort(key=lambda e: (e.tick, e.order))
    for index, e in enumerate(replaced.events):
        e.order = index
    return replaced
