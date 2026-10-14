"""Close the silence between two adjacent inferred arrangement clips.

This is a time-shifting operation, not a persistent region merge. The clips
are inferred from note gaps; moving the second clip flush with the first makes
it appear as one arrangement clip.
"""
from arrangement import track_clips
from batch_clip_ops import edit_clips
from midi import MidiError


def close_clip_gap(song, track_index, clip_index, gap=0, include_events=True):
    """Move next clip left to `gap` ticks after the current clip's end.

    Returns the number of moved notes. Does not change tempo/meta events.
    Validates everything before changing song data.
    """
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track')
    if not 0 < song.division < 0x8000:
        raise MidiError('PPQN timing required')
    if type(clip_index) is not int or clip_index < 0:
        raise MidiError('Invalid clip index')
    if type(gap) is not int or not 0 <= gap < song.division * 4:
        raise MidiError('Gap must be between zero and less than one bar')
    if type(include_events) is not bool:
        raise MidiError('include_events must be boolean')
    clips = track_clips(song.tracks[track_index], song.division)
    if clip_index + 1 >= len(clips):
        raise MidiError('No following clip to join')
    first_end = clips[clip_index][1]
    second_start = clips[clip_index + 1][0]
    delta = first_end + gap - second_start
    if delta >= 0:
        raise MidiError('Clips are already touching or overlapping')
    return edit_clips(song, [(track_index, clip_index + 1)], delta,
                      duplicate=False, include_events=include_events)
