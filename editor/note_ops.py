"""Non-destructive-style MIDI note operations for XGW Next.

All functions mutate the in-memory Song and mark it dirty. The GUI owns undo
snapshots. Callers should validate edits before snapshotting when practical.
"""
from collections import defaultdict, deque
from midi import Event, MidiError

def paired_notes(track):
    """Return (on_index, off_index) pairs, matched FIFO per channel/pitch."""
    pending = defaultdict(deque)
    pairs = []
    for index, e in sorted(enumerate(track.events), key=lambda pair: (pair[1].tick, pair[1].order)):
        if not 0x80 <= e.status <= 0x9f or len(e.data) != 2:
            continue
        key = (e.status & 15, e.data[0])
        if e.status & 0xf0 == 0x90 and e.data[1] > 0:
            pending[key].append(index)
        elif pending[key]:
            pairs.append((pending[key].popleft(), index))
    return pairs

def _division(song):
    if song.division & 0x8000:
        raise MidiError("SMPTE time division is not supported by beat-grid editing")
    if not song.division:
        raise MidiError("Invalid ticks per quarter note")
    return song.division

def quantize_tick(tick, grid):
    if grid <= 0:
        raise MidiError("Grid must be positive")
    if tick < 0:
        raise MidiError("Tick cannot be negative")
    return ((tick + grid // 2) // grid) * grid

def quantize_notes(song, track_index, denominator=16, strength=100):
    """Quantize note starts; preserve note duration. denominator: 4,8,16,32,64."""
    division = _division(song)
    if denominator not in (4, 8, 16, 32, 64):
        raise MidiError("Unsupported quantization denominator")
    if not 0 <= strength <= 100:
        raise MidiError("Strength must be 0..100")
    grid = division * 4 // denominator
    if grid < 1:
        raise MidiError("Grid finer than MIDI tick resolution")
    track = song.tracks[track_index]
    changes = []
    for on_idx, off_idx in paired_notes(track):
        on, off = track.events[on_idx], track.events[off_idx]
        target = quantize_tick(on.tick, grid)
        delta = round((target - on.tick) * strength / 100)
        if on.tick + delta < 0 or off.tick + delta < 0:
            raise MidiError("Quantize would create a negative tick")
        changes.append((on, off, delta))
    for on, off, delta in changes:
        on.tick += delta
        off.tick += delta
    if any(delta for _, _, delta in changes):
        song.dirty = True
    return sum(bool(delta) for _, _, delta in changes)

def insert_note(song, track_index, tick, duration, pitch, velocity=100, channel=1):
    if not 0 <= tick or duration <= 0 or tick + duration > 0x0fffffff:
        raise MidiError("Invalid note timing")
    if not 0 <= pitch <= 127 or not 1 <= velocity <= 127 or not 1 <= channel <= 16:
        raise MidiError("Invalid note pitch, velocity or channel")
    track = song.tracks[track_index]
    order = max((e.order for e in track.events), default=-1) + 1
    ch = channel - 1
    for e in track.events:
        if e.status == 0xff and e.meta_type == 0x2f and e.tick < tick + duration:
            e.tick = tick + duration
    track.events.extend((
        Event(tick, 0x90 | ch, bytes((pitch, velocity)), order=order),
        Event(tick + duration, 0x80 | ch, bytes((pitch, 0)), order=order + 1),
    ))
    song.dirty = True
    return 2

def delete_note(song, track_index, on_index, off_index):
    track = song.tracks[track_index]
    if (on_index, off_index) not in paired_notes(track):
        raise MidiError("Selected events do not form a matched note")
    for index in sorted((on_index, off_index), reverse=True):
        del track.events[index]
    song.dirty = True
    return 2

def move_note(song, track_index, on_index, off_index, tick, pitch):
    track = song.tracks[track_index]
    if (on_index, off_index) not in paired_notes(track):
        raise MidiError("Selected events do not form a matched note")
    if tick < 0 or not 0 <= pitch <= 127:
        raise MidiError("Invalid target position or pitch")
    on, off = track.events[on_index], track.events[off_index]
    duration = off.tick - on.tick
    if duration < 0 or tick + duration > 0x0fffffff:
        raise MidiError("Invalid resulting note duration")
    on.tick, off.tick = tick, tick + duration
    on.data = bytes((pitch, on.data[1]))
    off.data = bytes((pitch, off.data[1]))
    song.dirty = True

def resize_note(song, track_index, on_index, off_index, new_end_tick):
    """Change note duration while preserving start, pitch, channel and velocity."""
    track = song.tracks[track_index]
    if (on_index, off_index) not in paired_notes(track):
        raise MidiError("Selected events do not form a matched note")
    on = track.events[on_index]
    if not on.tick < new_end_tick <= 0x0fffffff:
        raise MidiError("Note end must be after its start and within MIDI limits")
    track.events[off_index].tick = new_end_tick
    song.dirty = True
    return new_end_tick - on.tick

def transform_notes(song, track_index, pairs, delta_ticks=0, delta_pitch=0, duplicate=False):
    """Atomically move or duplicate a selection of matched note pairs."""
    track = song.tracks[track_index]
    valid = set(paired_notes(track))
    chosen = list(dict.fromkeys(tuple(pair) for pair in pairs))
    if not chosen or any(pair not in valid for pair in chosen):
        raise MidiError("Invalid note selection")
    updates = []
    for on_idx, off_idx in chosen:
        on, off = track.events[on_idx], track.events[off_idx]
        pitch = on.data[0] + delta_pitch
        start, end = on.tick + delta_ticks, off.tick + delta_ticks
        if not 0 <= pitch <= 127 or not 0 <= start <= end <= 0x0fffffff:
            raise MidiError("Note movement exceeds MIDI pitch or time range")
        updates.append((on, off, start, end, pitch))
    if not duplicate and delta_ticks == 0 and delta_pitch == 0:
        return 0
    if duplicate:
        order = max((e.order for e in track.events), default=-1) + 1
        for on, off, start, end, pitch in updates:
            track.events.append(Event(start, on.status, bytes((pitch, on.data[1])),
                                      on.meta_type, order))
            track.events.append(Event(end, off.status, bytes((pitch, off.data[1])),
                                      off.meta_type, order + 1))
            order += 2
    else:
        for on, off, start, end, pitch in updates:
            on.tick, off.tick = start, end
            on.data = bytes((pitch, on.data[1]))
            off.data = bytes((pitch, off.data[1]))
    song.dirty = True
    return len(updates)

def delete_notes(song, track_index, pairs):
    """Delete a validated group of notes as one edit."""
    track = song.tracks[track_index]
    valid = set(paired_notes(track))
    chosen = list(dict.fromkeys(tuple(pair) for pair in pairs))
    if not chosen or any(pair not in valid for pair in chosen):
        raise MidiError("Invalid note selection")
    indices = sorted({i for pair in chosen for i in pair}, reverse=True)
    for index in indices:
        del track.events[index]
    song.dirty = True
    return len(chosen)
