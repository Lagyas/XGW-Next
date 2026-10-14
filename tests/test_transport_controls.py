import unittest
from types import SimpleNamespace
from app import App
from sequencer_view import SequencerView, LEFT_WIDTH, BEAT_WIDTH

class Var:
    def __init__(self, value): self.value = str(value)
    def get(self): return self.value
    def set(self, value): self.value = str(value)

class TransportTests(unittest.TestCase):
    def test_locator_values(self):
        self.assertEqual(App._safe_locator('120'), 120)
        self.assertEqual(App._safe_locator('-1'), 0)
        self.assertEqual(App._safe_locator('oops'), 0)

    def test_ruler_tick_clamps_to_zero(self):
        view = SimpleNamespace(song=SimpleNamespace(division=480),
                               canvas=SimpleNamespace(canvasx=lambda x: x))
        self.assertEqual(SequencerView.ruler_tick(view, SimpleNamespace(x=LEFT_WIDTH + BEAT_WIDTH, y=0)), 480)
        self.assertEqual(SequencerView.ruler_tick(view, SimpleNamespace(x=0, y=0)), 0)

    def test_set_left_locator_extends_right(self):
        drawn = []
        view = SimpleNamespace(locator_left=0, locator_right=0, draw=lambda: drawn.append(True))
        app = SimpleNamespace(song=SimpleNamespace(division=480), playhead_tick=900,
                              loop_start=Var(0), loop_end=Var(500), sequencer=view,
                              _safe_locator=App._safe_locator)
        App.set_locator(app, 'L')
        self.assertEqual(app.loop_start.get(), '900')
        self.assertEqual(app.loop_end.get(), '1380')
        self.assertTrue(drawn)

    def test_set_right_locator_moves_left_if_needed(self):
        view = SimpleNamespace(locator_left=0, locator_right=0, draw=lambda: None)
        app = SimpleNamespace(song=SimpleNamespace(division=480), playhead_tick=100,
                              loop_start=Var(500), loop_end=Var(1000), sequencer=view,
                              _safe_locator=App._safe_locator)
        App.set_locator(app, 'R')
        self.assertEqual(app.loop_start.get(), '0')
        self.assertEqual(app.loop_end.get(), '100')
