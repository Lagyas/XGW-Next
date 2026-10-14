"""Basic staff positioning from MIDI note pitches (C major spelling)."""
from midi import MidiError
from note_ops import paired_notes

PITCH_STEPS = ((0, False), (0, True), (1, False), (1, True),
               (2, False), (3, False), (3, True), (4, False),
               (4, True), (5, False), (5, True), (6, False))

def staff_position(pitch, clef="treble"):
    """Diatonic steps above the bottom staff line, and sharp indicator."""
    if type(pitch) is not int or not 0 <= pitch <= 127:
        raise MidiError("Invalid MIDI pitch")
    if clef not in ("treble", "bass"):
        raise MidiError("Unsupported clef")
    octave, pitch_class = divmod(pitch, 12)
    degree, sharp = PITCH_STEPS[pitch_class]
    # Treble bottom line E4 (64), bass bottom line G2 (43).
    return octave * 7 + degree - (37 if clef == "treble" else 25), sharp

def staff_notes(track, channel=None):
    """Return matched note spans, without modifying the source track."""
    if channel is not None and (type(channel) is not int or not 0 <= channel <= 15):
        raise MidiError("Channel must be 0–15")
    notes = []
    for on_idx, off_idx in paired_notes(track):
        on, off = track.events[on_idx], track.events[off_idx]
        ch = on.status & 15
        if channel is None or ch == channel:
            notes.append((on.tick, off.tick, on.data[0], on.data[1], ch))
    return sorted(notes, key=lambda n: (n[0], n[2], n[4]))


def note_value(duration_ticks, division):
    """Choose the closest standard notation value, without changing MIDI timing.

    Returns (denominator, dotted). Tuple values describe a visual approximation
    and do not imply quantization of the underlying note.
    """
    if type(duration_ticks) is not int or duration_ticks <= 0:
        raise MidiError("Note duration must be positive integer ticks")
    if type(division) is not int or not 1 <= division <= 0x7fff:
        raise MidiError("Notation requires PPQN division")
    candidates = []
    for denominator in (1, 2, 4, 8, 16, 32, 64):
        for dotted in (False, True):
            beats = 4 / denominator * (1.5 if dotted else 1)
            candidates.append((abs(duration_ticks / division - beats),
                               denominator, dotted))
    _, denominator, dotted = min(candidates, key=lambda c: (c[0], c[2], c[1]))
    return denominator, dotted


def staff_rest_spans(notes, division, end_tick=None):
    """Return silent spans in a track, accounting for overlapping notes.

    Notes are (start, end, pitch, velocity, channel). Silence is measured
    across the whole displayed track, not separately for each MIDI channel.
    Rests are not inferred after the last note unless end_tick is supplied.
    """
    if type(division) is not int or not 1 <= division <= 0x7fff:
        raise MidiError("Notation requires PPQN division")
    if end_tick is not None and (type(end_tick) is not int or end_tick < 0):
        raise MidiError("Invalid end tick")
    intervals = []
    for start, end, *_ in notes:
        if (type(start) is not int or type(end) is not int
                or start < 0 or end < start):
            raise MidiError("Invalid note interval")
        if end > start:
            intervals.append((start, end))
    cursor = 0
    rests = []
    for start, end in sorted(intervals):
        if start > cursor:
            rests.append((cursor, start))
        cursor = max(cursor, end)
    if end_tick is not None and end_tick > cursor:
        rests.append((cursor, end_tick))
    return rests
