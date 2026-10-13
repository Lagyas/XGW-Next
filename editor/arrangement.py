"""Extract display-only MIDI arrangement clips from paired notes.

A gap of at least one bar separates two clips. No MIDI data is changed.
"""
from note_ops import paired_notes

def track_clips(track, division, gap_bars=1):
    if division <= 0 or division & 0x8000:
        return []
    notes = []
    for on_idx, off_idx in paired_notes(track):
        on, off = track.events[on_idx], track.events[off_idx]
        notes.append((on.tick, max(on.tick + 1, off.tick)))
    notes.sort()
    if not notes:
        return []
    gap = max(1, division * 4 * gap_bars)
    clips = []
    start, end = notes[0]
    for note_start, note_end in notes[1:]:
        if note_start - end >= gap:
            clips.append((start, end))
            start, end = note_start, note_end
        else:
            end = max(end, note_end)
    clips.append((start, end))
    return clips
