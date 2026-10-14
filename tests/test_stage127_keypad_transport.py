import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from app import App

class KeypadTransportTests(unittest.TestCase):
    def make_app(self):
        app = object.__new__(App)
        app.song = object()
        app.recorder = SimpleNamespace(recording=False)
        app.playhead_tick = 123
        app.loop_start = SimpleNamespace(get=lambda: '24')
        app.loop_end = SimpleNamespace(get=lambda: '480')
        app._cursor_bookmark_tick = None
        app.seek_to_tick = Mock()
        app.status = SimpleNamespace(set=Mock())
        return app

    def test_numpad_jumps(self):
        app = self.make_app()
        event = SimpleNamespace(widget=SimpleNamespace(winfo_class=lambda: 'Canvas'))
        for key, target in ((0,0),(1,24),(3,480)):
            self.assertEqual(App._numpad_transport(app,event,key),'break')
            app.seek_to_tick.assert_called_with(target, locator_jump=True)

    def test_two_bookmarks_position(self):
        app = self.make_app()
        event = SimpleNamespace(widget=SimpleNamespace(winfo_class=lambda: 'Canvas'))
        App._numpad_transport(app,event,2)
        self.assertEqual(app._cursor_bookmark_tick,123)
        app.playhead_tick = 999
        App._numpad_transport(app,event,2)
        app.seek_to_tick.assert_called_once_with(123,locator_jump=True)

    def test_ignores_entry(self):
        app = self.make_app()
        event = SimpleNamespace(widget=SimpleNamespace(winfo_class=lambda: 'TEntry'))
        self.assertIsNone(App._numpad_transport(app,event,0))
        app.seek_to_tick.assert_not_called()

    def test_space_stops_recording(self):
        app = self.make_app()
        app.player = SimpleNamespace(playing=False)
        app.recorder.recording = True
        app.stop_midi = Mock()
        event = SimpleNamespace(widget=SimpleNamespace(winfo_class=lambda: 'Canvas'))
        self.assertEqual(App._space_transport(app,event),'break')
        app.stop_midi.assert_called_once()

if __name__ == '__main__':
    unittest.main()
