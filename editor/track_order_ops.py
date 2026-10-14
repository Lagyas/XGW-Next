"""Atomic track-order edits with aligned routing and XWS source metadata."""
from midi import MidiError


def move_track(song, source, destination, routes=None, xws_properties=None):
    """Move one track, returning (remapped_routes, remapped_xws_properties).

    Indices are zero-based. MIDI events are never edited or channel-remapped.
    Validation happens before any mutation of the song.
    """
    n = len(song.tracks)
    if any(type(i) is not int or not 0 <= i < n for i in (source, destination)):
        raise MidiError('Invalid track position')
    from midi_routing import validate_routes
    old_routes = validate_routes(song, routes if routes is not None else {}, '')
    if xws_properties is not None:
        from xws_track_properties import validate_track_properties
        old_properties = validate_track_properties(xws_properties, n)
    else:
        old_properties = None
    order = list(range(n))
    order.insert(destination, order.pop(source))
    inverse = {old: new for new, old in enumerate(order)}
    new_routes = {inverse[old]: route for old, route in old_routes.items()}
    if old_properties is not None:
        new_properties = {'source': old_properties['source'], 'tracks': [
            {**row, 'track': inverse[row['track'] - 1] + 1}
            for row in old_properties['tracks']]}
        new_properties['tracks'].sort(key=lambda row: row['track'])
    else:
        new_properties = None
    if source != destination:
        song.tracks = [song.tracks[i] for i in order]
        song.dirty = True
    return new_routes, new_properties
