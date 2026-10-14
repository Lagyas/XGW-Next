"""Pure track-selection validation for the MIDI mixer destination."""


def destination_for_selection(song, selected_index, current_destination):
    """Follow a valid Track View selection without changing the song.

    Returns a 1-based destination track, retaining the existing selection
    when the view has no valid track selected.
    """
    if song is None or selected_index is None or isinstance(selected_index, bool):
        return current_destination
    if not isinstance(selected_index, int) or not 0 <= selected_index < len(song.tracks):
        return current_destination
    return selected_index + 1
