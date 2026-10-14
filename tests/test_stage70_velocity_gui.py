"""Smoke checks for shared velocity scaling controls without a display server."""
import inspect
from piano_roll import PianoRoll
from drum_editor import DrumEditor


def test_piano_velocity_scale_exposed():
    source = inspect.getsource(PianoRoll.scale_selected_velocity)
    assert 'scale_note_velocities' in source
    assert 'self.app.snapshot()' in source
    assert 'deepcopy(self.app.song)' in source


def test_drum_velocity_scale_exposed():
    source = inspect.getsource(DrumEditor.scale_velocity)
    assert 'scale_note_velocities' in source
    assert 'self.app.snapshot()' in source
    assert 'deepcopy(self.app.song)' in source
