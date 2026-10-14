"""Musical position formatting in XGworks-style bar:beat:tick notation."""
from fractions import Fraction
from midi import MidiError
from meter_grid import meter_changes


def tick_to_bbt(song, tick):
    """Return 1-based (bar, beat, sub-beat tick) for a PPQN song.

    A time-signature change starts a new bar, including when it occurs
    partway through the previous bar. Fraction arithmetic avoids drift.
    """
    if type(tick) is not int or tick < 0:
        raise MidiError('Song position must be a non-negative integer tick')
    changes = meter_changes(song)
    bar = 1
    for i, (start, numerator, denominator) in enumerate(changes):
        if start > tick:
            break
        next_tick = changes[i + 1][0] if i + 1 < len(changes) else None
        beat_length = Fraction(song.division * 4, denominator)
        measure_length = beat_length * numerator
        if next_tick is None or tick < next_tick:
            offset = Fraction(tick - start)
            bars, within = divmod(offset, measure_length)
            beat, remainder = divmod(within, beat_length)
            return (bar + int(bars), int(beat) + 1, int(remainder))
        elapsed = Fraction(next_tick - start)
        bar += int(-(-elapsed // measure_length))  # ceil: partial measure counts
    raise MidiError('Cannot resolve song position')


def format_bbt(song, tick):
    bar, beat, subtick = tick_to_bbt(song, tick)
    return f'{bar:04d}:{beat:02d}:{subtick:03d}'


def bbt_to_tick(song, bar, beat, subtick=0):
    """Resolve a bar:beat:tick position, respecting time-signature changes.

    Only canonical positions are accepted (not a beat past a short bar).
    """
    if any(type(v) is not int for v in (bar, beat, subtick)) or min(bar, beat) < 1 or subtick < 0:
        raise MidiError('Invalid bar:beat:tick position')
    changes = meter_changes(song)
    current_bar = 1
    for i, (start, numerator, denominator) in enumerate(changes):
        next_start = changes[i + 1][0] if i + 1 < len(changes) else None
        beat_len = Fraction(song.division * 4, denominator)
        measure_len = beat_len * numerator
        if next_start is None:
            segment_bars = None
        else:
            elapsed = Fraction(next_start - start)
            segment_bars = int(-(-elapsed // measure_len))
        if segment_bars is not None and bar >= current_bar + segment_bars:
            current_bar += segment_bars
            continue
        if beat > numerator or Fraction(subtick) >= beat_len:
            raise MidiError('Beat or tick is outside the current time signature')
        position = Fraction(start) + (bar - current_bar) * measure_len + (beat - 1) * beat_len + subtick
        if position.denominator != 1 or (next_start is not None and position >= next_start):
            raise MidiError('Position does not exist in this bar')
        result = int(position)
        if tick_to_bbt(song, result) != (bar, beat, subtick):
            raise MidiError('Position does not exist in this bar')
        return result
    raise MidiError('Cannot resolve song position')

def parse_bbt(song, value):
    """Parse a musical position in bar:beat:tick format."""
    try:
        parts = value.strip().split(':')
        if len(parts) != 3 or any(not part.isdecimal() for part in parts):
            raise ValueError
        return bbt_to_tick(song, *(int(part) for part in parts))
    except (ValueError, AttributeError) as exc:
        raise MidiError('Expected bar:beat:tick (e.g. 0002:01:000)') from exc
