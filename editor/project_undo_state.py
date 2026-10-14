"""Capture and restore non-SMF state together with MIDI undo snapshots."""
from copy import deepcopy

FIELDS = ('track_input_routes', 'track_routes', 'xws_track_properties', 'muted_tracks', 'solo_tracks',
          'muted_channels', 'solo_channels')


def capture(app):
    return {field: deepcopy(getattr(app, field, {} if field == "track_input_routes" else None)) for field in FIELDS}


def restore(app, state):
    if state is None:
        return
    for field in FIELDS:
        if field in state:
            setattr(app, field, deepcopy(state[field]))
