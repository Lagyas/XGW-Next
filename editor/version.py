"""Single source of the XGW Next version.

Bump FIX (and the CHANGELOG) with every "Beta N Fix M" change; the git tag is
`TAG`. Builds also record the git commit and build date (tools/write_build_info.py
writes editor/build_info.py before PyInstaller); a source run asks git.
"""
import platform
import subprocess
import sys
from pathlib import Path

MAJOR, MINOR, PATCH = 0, 4, 0
STAGE = "Beta 1"
FIX = 13

VERSION = f"{MAJOR}.{MINOR}.{PATCH}"
FULL_VERSION = f"{VERSION}-beta1.{FIX}"
TAG = f"v{FULL_VERSION}"


def build_info():
    """{'commit', 'dirty', 'date', 'source'} of this build (best effort)."""
    try:
        import build_info as info  # written by tools/write_build_info.py
        return {"commit": info.COMMIT, "dirty": info.DIRTY, "date": info.BUILD_DATE, "source": "build"}
    except ImportError:
        pass
    root = Path(__file__).resolve().parent.parent
    commit, dirty = "unknown", False
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True,
                                text=True, timeout=3).stdout.strip() or "unknown"
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root,
                                    capture_output=True, text=True, timeout=3).stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return {"commit": commit, "dirty": dirty, "date": "", "source": "source"}


def version_label(info=None):
    """'0.4.0 Beta 1 Fix 12 (d65cbee)' — for the window title."""
    info = info or build_info()
    commit = info["commit"] + ("+changes" if info.get("dirty") else "")
    return f"{VERSION} {STAGE} Fix {FIX} ({commit})"


def about_text(info=None):
    info = info or build_info()
    try:
        import tkinter
        tk_version = str(tkinter.TkVersion)
    except ImportError:
        tk_version = "?"
    lines = [
        f"XGW Next {VERSION} — {STAGE} Fix {FIX}",
        f"Version: {FULL_VERSION}  (git tag {TAG})",
        f"Commit: {info['commit']}{' (with local changes)' if info.get('dirty') else ''}",
        f"Build: {info['date'] or 'run from source'}",
        f"Python {platform.python_version()} · Tk {tk_version} · {platform.system()} {platform.release()} ({platform.machine()})",
        f"Executable: {'packaged app' if getattr(sys, 'frozen', False) else 'source'}",
    ]
    return "\n".join(lines)
