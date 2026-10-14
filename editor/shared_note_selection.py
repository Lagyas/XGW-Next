"""Cross-editor note selection with stable event identities.

Event UUIDs survive deepcopy, sorting and in-place edits. Imported SMF events
receive new session UUIDs; SMF does not encode editor-specific identifiers.
"""
from midi import MidiError

class SharedNoteSelection:
    def __init__(self):
        self.track = None
        self.pairs = frozenset()
        self.identities = frozenset()

    @staticmethod
    def _identity(pair, events):
        if events is None:
            return None
        a, b = pair
        if a >= len(events) or b >= len(events):
            return None
        return (events[a].uid, events[b].uid)

    def set(self, track, pairs, events=None):
        if type(track) is not int or track < 0:
            raise MidiError('Invalid selection track')
        result = set()
        for pair in pairs:
            if not isinstance(pair, (tuple, list)) or len(pair) != 2 or any(
                type(index) is not int or index < 0 for index in pair
            ) or pair[0] == pair[1]:
                raise MidiError('Invalid note event pair')
            result.add(tuple(pair))
        identities = {identity for pair in result
                      if (identity := self._identity(pair, events)) is not None}
        self.track, self.pairs, self.identities = track, frozenset(result), frozenset(identities)

    def get(self, track, notes, events=None):
        if track != self.track:
            return set()
        if events is not None and self.identities:
            return {(note[5], note[6]) for note in notes
                    if self._identity((note[5], note[6]), events) in self.identities}
        if self.identities:
            return set()  # Never fall back to stale indices for UUID-backed selections.
        return {(note[5], note[6]) for note in notes if (note[5], note[6]) in self.pairs}

    def reconcile(self, track, notes, events=None):
        if track != self.track:
            return set()
        result = self.get(track, notes, events)
        self.pairs = frozenset(result)
        if events is not None and self.identities:
            self.identities = frozenset(self._identity(pair, events) for pair in result)
        return result

    def clear(self):
        self.track, self.pairs, self.identities = None, frozenset(), frozenset()


def reconcile_editor_pairs(selected_pairs, notes, events, shared, track):
    """Resolve selected notes after event reordering using stable MIDI event UIDs.

    If a cross-editor UUID selection exists, it is authoritative; otherwise
    retain only pairs still present in the current note extraction.
    """
    available = {(note[5], note[6]) for note in notes}
    if shared is not None and shared.track == track and shared.identities:
        return shared.get(track, notes, events)
    return set(selected_pairs) & available
