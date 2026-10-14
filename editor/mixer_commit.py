"""Atomic, validated mixer edits shared by the GUI and regression tests."""
from copy import deepcopy
from midi import MidiError
from mixer_ops import set_mixer_batch


def preview_mixer_commit(song, track_index, updates, tick):
    """Return a changed copy; on failure the caller's song remains untouched."""
    if song is None:
        raise MidiError('No MIDI song loaded')
    if not isinstance(updates, dict) or not updates:
        raise MidiError('No mixer changes to apply')
    preview = deepcopy(song)
    count = set_mixer_batch(preview, track_index, updates, tick)
    return preview, count


def mixer_changes(displayed, baseline):
    """Collect changed CC values without silently accepting bad GUI input."""
    from mixer_ops import MIXER_CONTROLLERS
    if not isinstance(displayed, dict) or not isinstance(baseline, dict):
        raise MidiError('Invalid mixer state')
    changes = {}
    for channel, values in displayed.items():
        if type(channel) is not int or not 1 <= channel <= 16 or not isinstance(values, dict):
            raise MidiError('Invalid mixer channel')
        prior = baseline.get(channel, {})
        for name, value in values.items():
            if name not in MIXER_CONTROLLERS or type(value) is not int or not 0 <= value <= 127:
                raise MidiError(f'CH {channel} {name}: invalid controller value')
            if value != prior.get(name):
                changes.setdefault(channel, {})[name] = value
    return changes
