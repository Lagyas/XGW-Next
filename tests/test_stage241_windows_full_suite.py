"""Windows build and verification must exercise pytest-only regression tests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WindowsFullSuiteTests(unittest.TestCase):
    def test_build_installs_pytest(self):
        content = (ROOT / 'build-local-windows.bat').read_text(encoding='utf-8')
        self.assertIn('"pytest>=8,<10"', content)

    def test_build_runs_full_pytest_suite_before_packaging(self):
        content = (ROOT / 'build-local-windows.bat').read_text(encoding='utf-8')
        self.assertIn('python -m pytest tests -q', content)
        self.assertLess(content.index('python -m pytest tests -q'), content.index('python -m PyInstaller'))

    def test_verify_runs_full_pytest_suite(self):
        content = (ROOT / 'verify-windows-beta.bat').read_text(encoding='utf-8')
        self.assertIn('".venv\\Scripts\\python.exe" -m pytest tests -q', content)
        self.assertNotIn('unittest discover', content)

if __name__ == '__main__':
    unittest.main()
