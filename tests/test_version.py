"""Version numbering (Beta 1 Fix 13)."""
import re
from pathlib import Path

import version

ROOT = Path(__file__).resolve().parents[1]


def test_version_strings_are_consistent():
    assert re.fullmatch(r"\d+\.\d+\.\d+", version.VERSION)
    assert version.FULL_VERSION == f"{version.VERSION}-beta1.{version.FIX}"
    assert version.TAG == "v" + version.FULL_VERSION


def test_changelog_lists_the_current_fix():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"| {version.FIX} | {version.TAG} |" in changelog


def test_label_and_about_show_commit():
    info = {"commit": "abc1234", "dirty": True, "date": "2026-10-20 10:00 UTC on Darwin", "source": "build"}
    label = version.version_label(info)
    assert label == f"{version.VERSION} {version.STAGE} Fix {version.FIX} (abc1234+changes)"
    about = version.about_text(info)
    assert "abc1234" in about and "2026-10-20" in about and version.TAG in about


def test_build_info_falls_back_without_generated_file():
    info = version.build_info()
    assert set(info) == {"commit", "dirty", "date", "source"}
    assert info["commit"]


def test_every_build_records_version_info():
    for name in ("build-local-windows.bat", "build-local-macos.sh", ".github/workflows/build-apps.yml"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "write_build_info.py" in text, name
