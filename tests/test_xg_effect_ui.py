"""Guard against Tk callbacks referenced before their nested definitions."""
import ast
from pathlib import Path
import unittest


class XGEffectUITests(unittest.TestCase):
    def test_inspector_callback_defined_before_button(self):
        path = Path(__file__).resolve().parents[1] / "editor" / "xg_part_editor.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        editor = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                      and n.name == "XGPartEditor")
        method = next(n for n in editor.body if isinstance(n, ast.FunctionDef)
                      and n.name == "open_effects")
        definition_index = next(i for i, node in enumerate(method.body)
                                if isinstance(node, ast.FunctionDef)
                                and node.name == "inspect_parameters")
        callback_indices = [i for i, node in enumerate(method.body)
                            if isinstance(node, ast.Expr)
                            and any(isinstance(child, ast.keyword)
                                    and child.arg == "command"
                                    and isinstance(child.value, ast.Name)
                                    and child.value.id == "inspect_parameters"
                                    for child in ast.walk(node))]
        self.assertEqual(len(callback_indices), 1)
        self.assertLess(definition_index, callback_indices[0])
