"""Piano Roll undo/redo actions work without a running Tk display."""
from piano_roll import PianoRoll


class App:
    def __init__(self):
        self.history = [1]
        self.redo_history = [2]
        self.calls = []

    def undo(self):
        self.calls.append('undo')

    def redo(self):
        self.calls.append('redo')


class Info:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


def roll_stub(app):
    class Stub:
        undo_note_edit = PianoRoll.undo_note_edit
        redo_note_edit = PianoRoll.redo_note_edit

        def __init__(self):
            self.app = app
            self.selected = 3
            self.selected_pairs = {(1, 2)}
            self.info = Info()
            self.renders = 0

        def render(self):
            self.renders += 1

    return Stub()


def test_undo_clears_selection_and_refreshes():
    app = App()
    roll = roll_stub(app)
    roll.undo_note_edit()
    assert app.calls == ['undo']
    assert roll.selected is None and not roll.selected_pairs
    assert roll.renders == 1


def test_redo_clears_selection_and_refreshes():
    app = App()
    roll = roll_stub(app)
    roll.redo_note_edit()
    assert app.calls == ['redo']
    assert roll.selected is None and not roll.selected_pairs
    assert roll.renders == 1


def test_no_history_does_not_redraw():
    app = App()
    app.history.clear()
    app.redo_history.clear()
    roll = roll_stub(app)
    roll.undo_note_edit()
    roll.redo_note_edit()
    assert not app.calls and roll.renders == 0
