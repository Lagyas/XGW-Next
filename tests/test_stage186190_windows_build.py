"""Static build/release contract tests (can run on Linux CI)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class WindowsBuildTests(unittest.TestCase):
    def test_spec_targets_app(self):
        spec = (ROOT / 'XGW-Next.spec').read_text(encoding='utf-8')
        self.assertIn("['editor/app.py']", spec)
        self.assertIn("name='XGW-Next'", spec)
        self.assertIn('collect_submodules', spec)

    def test_build_uses_checked_in_spec(self):
        script = (ROOT / 'build-local-windows.bat').read_text(encoding='utf-8')
        self.assertIn('PyInstaller --noconfirm --clean XGW-Next.spec', script)
        self.assertIn('python -m pytest tests -q', script)
        self.assertIn('if errorlevel 1', script)

    def test_build_checks_artifact(self):
        script = (ROOT / 'build-local-windows.bat').read_text(encoding='utf-8')
        self.assertIn('dist\\XGW-Next.exe', script)
        self.assertIn('%%~zF LEQ 0', script)

    def test_start_uses_project_virtualenv(self):
        script = (ROOT / 'START_WINDOWS.bat').read_text(encoding='utf-8')
        self.assertIn('.venv\\Scripts\\python.exe', script)
        self.assertIn('editor\\app.py', script)

    def test_no_build_after_test_failure(self):
        script = (ROOT / 'build-local-windows.bat').read_text(encoding='utf-8')
        self.assertLess(script.index('python -m pytest tests -q'), script.index('PyInstaller --noconfirm'))

if __name__ == '__main__':
    unittest.main()
