"""Explicit, non-destructive arrangement boundaries for a track.

SMF has no standard clip objects. These boundaries live in the editing session;
exporting MIDI preserves notes but cannot preserve clip regions.
"""
from arrangement import track_clips
from midi import MidiError
from uuid import uuid4


def _check(song, track_index):
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track')
    if not 0 < song.division < 0x8000:
        raise MidiError('PPQN timing required')
    return song.tracks[track_index]


def split_region(song, track_index, clip_index, tick):
    """Split an arrangement region without modifying MIDI notes or automation."""
    track = _check(song, track_index)
    clips = track_clips(track, song.division)
    if type(clip_index) is not int or not 0 <= clip_index < len(clips):
        raise MidiError('Invalid clip')
    start, end = clips[clip_index]
    if type(tick) is not int or not start < tick < end:
        raise MidiError('Split point must be inside clip')
    regions = list(clips)
    regions[clip_index:clip_index+1] = [(start, tick), (tick, end)]
    ids = getattr(track, 'clip_region_ids', None)
    if not isinstance(ids, list) or len(ids) != len(clips):
        ids = [uuid4().hex for _ in clips]
    ids = list(ids)
    ids[clip_index:clip_index+1] = [ids[clip_index], uuid4().hex]
    track.clip_regions = regions
    track.clip_region_ids = ids
    return len(regions)


def merge_regions(song, track_index, clip_index):
    """Merge two adjacent regions, preserving silence and all MIDI data."""
    track = _check(song, track_index)
    clips = track_clips(track, song.division)
    if type(clip_index) is not int or not 0 <= clip_index + 1 < len(clips):
        raise MidiError('No following clip to merge')
    left, right = clips[clip_index], clips[clip_index+1]
    if left[1] > right[0]:
        raise MidiError('Overlapping regions cannot be merged')
    regions = list(clips)
    regions[clip_index:clip_index+2] = [(left[0], right[1])]
    ids = getattr(track, 'clip_region_ids', None)
    if not isinstance(ids, list) or len(ids) != len(clips):
        ids = [uuid4().hex for _ in clips]
    ids = list(ids)
    ids[clip_index:clip_index+2] = [ids[clip_index]]
    track.clip_regions = regions
    track.clip_region_ids = ids
    return len(regions)


def reset_regions(song, track_index):
    track = _check(song, track_index)
    if hasattr(track, 'clip_region_ids'):
        del track.clip_region_ids
    if hasattr(track, 'clip_regions'):
        del track.clip_regions
    return track_clips(track, song.division)
