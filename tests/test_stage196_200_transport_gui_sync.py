"""Regression checks for synchronous seek/locator GUI updates (headless)."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from app import App

class Var:
    def __init__(self, value=''): self.value = str(value)
    def get(self): return self.value
    def set(self, value): self.value = str(value)

class TransportGuiSyncTests(unittest.TestCase):
    def _app(self, window=True):
        calls = []
        piano = SimpleNamespace(winfo_exists=lambda: True, update_playhead=lambda: calls.append('piano'))
        win = SimpleNamespace(winfo_exists=lambda: True) if window else None
        obj = SimpleNamespace(song=SimpleNamespace(division=480), recorder=SimpleNamespace(recording=False),
            player=SimpleNamespace(playing=False), loop_enabled=Var(0), loop_start=Var(0),
            loop_end=Var(1920), playhead_tick=0, play_start_tick=Var(0),
            position_text=Var(), transport_position=Var(), transport_window=win,
            sequencer=SimpleNamespace(set_playhead=lambda tick, follow: calls.append(('seek',tick,follow))),
            workspace=SimpleNamespace(windows={'Piano Roll':piano}), _safe_locator=App._safe_locator)
        return obj,calls

    def test_seek_updates_all_surfaces_without_playback(self):
        obj,calls=self._app()
        with patch('app.format_bbt', return_value='0002:01:000'):
            App.seek_to_tick(obj, 480)
        self.assertEqual(obj.playhead_tick,480)
        self.assertEqual(obj.play_start_tick.get(),'480')
        self.assertIn('480 ticks',obj.position_text.get())
        self.assertEqual(obj.transport_position.get(),'0002:01:000')
        self.assertIn(('seek',480,True),calls)
        self.assertIn('piano',calls)

    def test_seek_without_transport_window(self):
        obj,calls=self._app(False)
        with patch('app.format_bbt', return_value='0001:02:000'):
            App.seek_to_tick(obj, 240)
        self.assertEqual(obj.playhead_tick,240)
        self.assertIn('piano',calls)

    def test_locator_does_not_require_transport_window_attribute(self):
        obj=SimpleNamespace(song=SimpleNamespace(division=480), playhead_tick=100,
            loop_start=Var(0),loop_end=Var(1000),
            sequencer=SimpleNamespace(locator_left=0,locator_right=0,draw=lambda:None))
        App.set_locator(obj,'L')
        self.assertEqual(obj.loop_start.get(),'100')

if __name__ == '__main__': unittest.main()
