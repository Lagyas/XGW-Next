import ast
import pathlib
import unittest


class XGSnapshotGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = pathlib.Path(__file__).resolve().parents[1] / 'editor' / 'xg_part_editor.py'
        cls.tree = ast.parse(source.read_text(encoding='utf-8'))
        cls.methods = {node.name: node for node in ast.walk(cls.tree)
                       if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def test_snapshot_action_exists(self):
        self.assertIn('show_snapshot', self.methods)

    def test_snapshot_uses_read_only_engine(self):
        calls = [node.func.id for node in ast.walk(self.methods['show_snapshot'])
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        self.assertIn('effect_parameters_at_tick', calls)
        self.assertNotIn('write_effect_parameter_to_song', calls)

    def test_snapshot_has_cancel_guard(self):
        self.assertTrue(any(isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                            for node in ast.walk(self.methods['show_snapshot'])))
