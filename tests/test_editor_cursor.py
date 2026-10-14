import pytest
from editor_cursor import ruler_tick, seek_editor
from midi import MidiError

def test_origin():
    assert ruler_tick(68, 68, 64, 480) == 0

def test_beat():
    assert ruler_tick(132, 68, 64, 480) == 480

def test_negative_clamped():
    assert ruler_tick(0, 68, 64, 480) == 0

def test_snap():
    assert ruler_tick(104, 68, 64, 480, '1/16') == 240

def test_bad_division():
    with pytest.raises(MidiError):
        ruler_tick(100, 68, 64, 0)

class Stub:
    song = object()
    def __init__(self, recording=False):
        self.recorder = type('Recorder', (), {'recording': recording})()
        self.tick = None
    def seek_to_tick(self, tick):
        self.tick = tick

def test_shared_seek():
    app = Stub()
    assert seek_editor(app, 960) is True
    assert app.tick == 960

def test_recording_guard():
    app = Stub(True)
    assert seek_editor(app, 960) is False
    assert app.tick is None
