"""Real Tk integration smoke test (runs in a virtual X display on Linux)."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.skipif(sys.platform != 'linux' or not shutil.which('xvfb-run'),
                    reason='requires Linux with xvfb-run')
def test_main_editors_open_refresh_undo_and_reopen():
    code = r'''
import tkinter as tk
from app import App
from midi import Song, Track, Event
root = tk.Tk()
app = App(root)
app.song = Song(1, 480, [Track([
    Event(0, 0x99, bytes([36, 100])), Event(240, 0x89, bytes([36, 0])),
    Event(0, 0x90, bytes([60, 90])), Event(480, 0x80, bytes([60, 0])),
    Event(0, 0xB0, bytes([7, 100]))])])
app.refresh()
root.update()
for kind, opener in [('Piano Roll', app.open_piano_roll),
                     ('Drum Editor', app.open_drum_editor),
                     ('List Editor', app.open_list_editor),
                     ('MIDI Mixer', app.open_midi_mixer),
                     ('XG Part Editor', app.open_xg_editor)]:
    opener()
    root.update()
    assert kind in app.workspace.windows
    assert app.workspace.windows[kind].winfo_exists()
app.snapshot()
app.song.tracks[0].events[0].tick = 120
app.song.dirty = True
app.undo()
root.update()
assert app.song.tracks[0].events[0].tick == 0
app.redo()
root.update()
assert app.song.tracks[0].events[0].tick == 120
app.workspace.close('Piano Roll')
app.open_piano_roll()
root.update()
assert app.workspace.windows['Piano Roll'].winfo_exists()
app.workspace.close_all()
root.destroy()
'''
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'editor')
    proc = subprocess.run(['xvfb-run', '-a', sys.executable, '-c', code],
                          cwd=ROOT, env=env, text=True, capture_output=True,
                          timeout=35, check=False)
    assert proc.returncode == 0, proc.stdout + '\n' + proc.stderr
