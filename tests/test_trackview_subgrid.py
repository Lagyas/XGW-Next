import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
from sequencer_view import visible_subdivision_ticks

def test_sixteenth_visible_at_high_zoom():
    assert visible_subdivision_ticks(480, "1/16", 80) == 120

def test_sixteenth_hidden_at_low_zoom():
    assert visible_subdivision_ticks(480, "1/16", 28) is None

def test_quarter_visible_at_low_zoom():
    assert visible_subdivision_ticks(480, "1/4", 28) == 480

def test_off_hides_subgrid():
    assert visible_subdivision_ticks(480, "Off", 80) is None
