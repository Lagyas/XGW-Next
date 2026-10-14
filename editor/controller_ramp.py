"""Generate a quantized controller ramp, without touching unrelated events."""
from midi import MidiError
from piano_cc_ops import insert_cc
from piano_pitch_ops import insert_pitch_bend


def ramp_points(start_tick, end_tick, start_value, end_value, step, maximum):
    if not all(type(n) is int for n in (start_tick, end_tick, start_value, end_value, step, maximum)):
        raise MidiError('Ramp arguments must be integers')
    if min(start_tick, end_tick) < 0 or step <= 0 or maximum <= 0:
        raise MidiError('Invalid ramp tick, grid or range')
    if not 0 <= start_value <= maximum or not 0 <= end_value <= maximum:
        raise MidiError('Ramp value outside MIDI range')
    lo, hi = sorted((start_tick, end_tick))
    if hi - lo > step * 10000:
        raise MidiError('Controller ramp is too long')
    ticks = list(range(lo, hi + 1, step))
    if ticks[-1] != hi:
        ticks.append(hi)
    if start_tick > end_tick:
        ticks.reverse()
    span = max(1, abs(end_tick - start_tick))
    return [(tick, round(start_value + (end_value - start_value) * abs(tick - start_tick) / span)) for tick in ticks]


def apply_ramp(song, track_index, lane, channel, points):
    if lane != 'pitch' and (type(lane) is not int or not 0 <= lane <= 127):
        raise MidiError('Invalid controller lane')
    for tick, value in points:
        if lane == 'pitch':
            insert_pitch_bend(song, track_index, tick, value, channel)
        else:
            insert_cc(song, track_index, tick, lane, value, channel)
