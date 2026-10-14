"""Bounded song snapshots with reversible undo and redo branches."""
from copy import deepcopy

class EditHistory:
    def __init__(self, limit=30):
        if type(limit) is not int or limit < 1:
            raise ValueError('History limit must be positive')
        self.limit = limit
        self.past = []
        self.future = []

    def checkpoint(self, song):
        if song is None:
            raise ValueError('No song to checkpoint')
        self.past.append(deepcopy(song))
        del self.past[:-self.limit]
        self.future.clear()

    def undo(self, current):
        if not self.past:
            return current, False
        self.future.append(deepcopy(current))
        del self.future[:-self.limit]
        return self.past.pop(), True

    def redo(self, current):
        if not self.future:
            return current, False
        self.past.append(deepcopy(current))
        del self.past[:-self.limit]
        return self.future.pop(), True

    def clear(self):
        self.past.clear()
        self.future.clear()
