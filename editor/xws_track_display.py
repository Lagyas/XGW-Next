"""Read-only source channel labels for the track routing interface."""
from xws_track_properties import validate_track_properties


def source_channel_labels(properties, track_count):
    """Return one label per MIDI track; do not infer routing from source metadata."""
    if type(track_count) is not int or track_count < 0:
        raise ValueError('Invalid track count')
    labels = ['—'] * track_count
    if properties is None:
        return tuple(labels)
    validated = validate_track_properties(properties, track_count)
    for row in validated['tracks']:
        labels[row['track'] - 1] = str(row['channel']) if row['verified'] else '?'
    return tuple(labels)
