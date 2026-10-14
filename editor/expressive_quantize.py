"""Atomic expressive MIDI note transforms (PPQN timelines only)."""
import random
from midi import MidiError
from note_ops import paired_notes, _division, quantize_tick

MAX_TICK = 0x0fffffff

def transform(song, track_index, *, pairs=None, denominator=16, strength=100,
              length=False, swing=0, timing_jitter=0, velocity_jitter=0, seed=None):
    """Quantize starts/optional lengths, swing offbeats and deterministic humanization.

    Selected pairs are event-index pairs, or None for all matched notes.
    Validation is atomic: invalid input never partially edits a song.
    """
    division = _division(song)
    if not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track')
    if denominator not in (4, 8, 16, 32, 64) or not isinstance(strength, int) or not 0 <= strength <= 100:
        raise MidiError('Invalid quantize grid or strength')
    if not isinstance(swing, int) or not -100 <= swing <= 100:
        raise MidiError('Swing must be -100..100')
    if not isinstance(timing_jitter, int) or not 0 <= timing_jitter <= 10000:
        raise MidiError('Invalid timing jitter')
    if not isinstance(velocity_jitter, int) or not 0 <= velocity_jitter <= 127:
        raise MidiError('Invalid velocity jitter')
    grid = division * 4 // denominator
    if grid < 1:
        raise MidiError('Grid finer than tick resolution')
    track = song.tracks[track_index]
    valid = paired_notes(track)
    if pairs is None:
        chosen = valid
    else:
        try:
            chosen = list(dict.fromkeys(tuple(pair) for pair in pairs))
        except (TypeError, ValueError) as exc:
            raise MidiError('Invalid note selection') from exc
        if any(pair not in valid for pair in chosen):
            raise MidiError('Invalid note selection')
    rng = random.Random(seed)
    changes = []
    for on_idx, off_idx in chosen:
        on, off = track.events[on_idx], track.events[off_idx]
        original_length = off.tick - on.tick
        if original_length <= 0:
            raise MidiError('Invalid note duration')
        target = quantize_tick(on.tick, grid)
        start = on.tick + round((target - on.tick) * strength / 100)
        # Every second grid subdivision is delayed by up to half a subdivision.
        if (target // grid) % 2:
            start += round(grid * swing / 200)
        if timing_jitter:
            start += rng.randint(-timing_jitter, timing_jitter)
        duration = original_length
        if length:
            target_length = max(grid, quantize_tick(original_length, grid))
            duration += round((target_length - duration) * strength / 100)
        end = start + duration
        if not 0 <= start < end <= MAX_TICK:
            raise MidiError('Transform would exceed MIDI tick limits')
        velocity = on.data[1]
        if velocity_jitter:
            velocity = max(1, min(127, velocity + rng.randint(-velocity_jitter, velocity_jitter)))
        changes.append((on, off, start, end, velocity))
    changed = 0
    for on, off, start, end, velocity in changes:
        if (on.tick, off.tick, on.data[1]) != (start, end, velocity):
            on.tick, off.tick = start, end
            on.data = bytes((on.data[0], velocity))
            changed += 1
    if changed:
        song.dirty = True
    return changed
