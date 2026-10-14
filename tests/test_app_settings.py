import tempfile
import unittest
from pathlib import Path
from app_settings import load_settings, save_settings


class SettingsTests(unittest.TestCase):
    def test_remembers_output_across_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            save_settings({"midi_output": "My USB MIDI OUT"}, path)
            self.assertEqual(load_settings(path)["midi_output"], "My USB MIDI OUT")

    def test_missing_or_invalid_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            self.assertEqual(load_settings(path), {})
            path.write_text("{bad json")
            self.assertEqual(load_settings(path), {})

    def test_unicode_output_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            save_settings({"midi_output": "Výstup 🎹"}, path)
            self.assertEqual(load_settings(path)["midi_output"], "Výstup 🎹")
