"""Shared editor-ruler coordinate conversion and transport seeking."""
from midi import MidiError

def ruler_tick(canvas_x, left, pixels_per_beat, division, snap=None):
    """Convert an absolute canvas x position to a nonnegative PPQN tick."""
    if not isinstance(division, int) or isinstance(division, bool) or not 0 < division < 0x8000:
        raise MidiError("PPQN timing required")
    if pixels_per_beat <= 0:
        raise MidiError("Invalid timeline scale")
    tick = max(0, round((canvas_x - left) * division / pixels_per_beat))
    if snap is not None:
        from snap_grid import snapped_tick
        tick = snapped_tick(tick, division, snap)
    return tick

def seek_editor(app, tick):
    """Use the application transport rather than changing a view-local cursor."""
    if app.song is None or app.recorder.recording:
        return False
    app.seek_to_tick(tick)
    return True
