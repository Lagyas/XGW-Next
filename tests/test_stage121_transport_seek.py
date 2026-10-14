"""Stage 121: seek/restart must wait for the MIDI worker to release its port."""
import ast
from pathlib import Path
import unittest


class TransportSeekSourceTests(unittest.TestCase):
    def test_seek_waits_for_worker_before_restarting(self):
        source = (Path(__file__).resolve().parents[1] / 'editor' / 'app.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        seek = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'seek_to_tick')
        calls = [node for node in ast.walk(seek) if isinstance(node, ast.Call)]
        def names(call):
            return ast.unparse(call.func)
        self.assertIn('self.player.wait_stopped', [names(c) for c in calls])
        self.assertIn('self.play_midi', [names(c) for c in calls])
