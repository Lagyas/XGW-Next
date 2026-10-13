"""Snap MIDI tick positions to an editable Piano Roll note grid."""
from midi import MidiError

SNAP_OPTIONS = ("Off", "1/4", "1/8", "1/16", "1/32", "1/64")

def snap_ticks(division, option):
    if division <= 0 or division & 0x8000:
        raise MidiError("Snap requires PPQN timing")
    if option == "Off":
        return None
    if option not in SNAP_OPTIONS:
        raise MidiError("Invalid snap resolution")
    denominator = int(option.split("/")[1])
    # A snap resolution finer than the source's PPQN cannot be represented.
    resolution = division * 4 // denominator
    if resolution < 1:
        raise MidiError("Snap grid is finer than one MIDI tick")
    return resolution

def snapped_tick(tick, division, option):
    if not 0 <= tick <= 0x0fffffff:
        raise MidiError("Invalid MIDI tick")
    resolution = snap_ticks(division, option)
    if resolution is None:
        return tick
    return min(0x0fffffff, ((tick + resolution // 2) // resolution) * resolution)
