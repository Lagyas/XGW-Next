"""Meter-aware beat and bar grid for MIDI sequencer windows.

A meter change starts a new bar at its exact tick, even mid-bar.
Tick coordinates always remain linear; tempo changes affect playback time,
not tick-to-pixel position.
"""
from fractions import Fraction
from midi import MidiError

def meter_changes(song):
    if song.division <= 0 or song.division & 0x8000:
        raise MidiError("Meter grid requires ticks-per-quarter-note division")
    found = []
    for track_index, track in enumerate(song.tracks):
        for event in track.events:
            if (event.status == 0xff and event.meta_type == 0x58
                    and len(event.data) >= 2 and event.tick >= 0):
                numerator, exponent = event.data[:2]
                if numerator and exponent <= 7:
                    found.append((event.tick, track_index, event.order,
                                  numerator, 1 << exponent))
    found.sort()
    changes = [(0, 4, 4)]
    for tick, _, _, numerator, denominator in found:
        if changes[-1][0] == tick:
            changes[-1] = (tick, numerator, denominator)
        else:
            changes.append((tick, numerator, denominator))
    return changes

def grid_lines(song, end_tick, max_lines=20000):
    """Return (tick, is_bar_start, bar_number) grid marks up to end_tick.

    Bars are numbered from 1; a new meter at a non-bar boundary starts
    the following bar. Fractions avoid drift for non-integer beat lengths.
    """
    changes = meter_changes(song)
    if end_tick < 0 or max_lines < 1:
        raise MidiError("Invalid timeline range")
    marks = []
    bar = 1
    current = Fraction(0)
    for segment, (start, numerator, denominator) in enumerate(changes):
        stop = (Fraction(changes[segment + 1][0])
                if segment + 1 < len(changes) else Fraction(end_tick + 1))
        if start > end_tick:
            break
        current = Fraction(start)
        beat = Fraction(song.division * 4, denominator)
        position = 0
        while current < stop and current <= end_tick:
            tick = round(current)
            if not marks or marks[-1][0] != tick:
                marks.append((tick, position == 0, bar))
                if len(marks) >= max_lines:
                    return marks
            current += beat
            position += 1
            if position >= numerator:
                position = 0
                bar += 1
        # Incomplete bars count as one bar when meter changes mid-bar.
        if segment + 1 < len(changes) and current > stop and position:
            bar += 1
        elif segment + 1 < len(changes) and current == stop and position:
            bar += 1
    return marks
