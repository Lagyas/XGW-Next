"""Atomic multi-track expressive MIDI transforms.

All tracks are validated on a temporary song before any source event changes.
"""
import copy
from midi import MidiError
from expressive_quantize import transform


def transform_tracks(song, track_indices, **options):
    try:
        indices = list(dict.fromkeys(track_indices))
    except (TypeError, ValueError) as exc:
        raise MidiError('Invalid track selection') from exc
    if not indices or any(not isinstance(i, int) or isinstance(i, bool) or
                          i < 0 or i >= len(song.tracks) for i in indices):
        raise MidiError('Invalid track selection')
    if 'pairs' in options:
        raise MidiError('Per-track note selection is not supported in batch mode')
    staged = copy.deepcopy(song)
    changed = 0
    for index in indices:
        changed += transform(staged, index, **options)
    if changed:
        for index in indices:
            for source, result in zip(song.tracks[index].events, staged.tracks[index].events):
                source.tick = result.tick
                source.data = result.data
        song.dirty = True
    return changed
