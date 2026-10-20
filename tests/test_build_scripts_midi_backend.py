"""Every PyInstaller build must bundle the dynamically imported mido rtmidi
backend, otherwise playback fails with "No module named mido.backends.rtmidi"."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_spec_bundles_rtmidi_backend():
    spec = (ROOT / "XGW-Next.spec").read_text(encoding="utf-8")
    assert "mido.backends.rtmidi" in spec


def test_command_line_builds_bundle_rtmidi_backend():
    for name in ("build-local-macos.sh", ".github/workflows/build-apps.yml"):
        text = (ROOT / name).read_text(encoding="utf-8")
        builds = [line for line in text.splitlines() if "PyInstaller" in line and "editor/app.py" in line]
        assert builds, name
        for line in builds:
            assert "--hidden-import mido.backends.rtmidi" in line, f"{name}: {line.strip()}"
            assert "--collect-submodules rtmidi" in line, f"{name}: {line.strip()}"
