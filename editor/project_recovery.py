"""Crash recovery snapshots kept outside the source project.

Recovery is intentionally opt-in on reopening: never overwrite the original.
"""
import hashlib
import json
from pathlib import Path
from app_settings import settings_path
from project_bundle import save_project, load_project


def recovery_path(source, directory=None):
    key = str(Path(source).expanduser().resolve()) if source else 'untitled'
    digest = hashlib.sha256(key.encode('utf-8')).hexdigest()[:24]
    base = Path(directory) if directory is not None else settings_path().parent / 'recovery'
    return base / (digest + '.xgwn')


def write_recovery(source, song, routes=None, output='', workspace=None, directory=None, xws_track_properties=None, midi_inputs=None):
    target = recovery_path(source, directory)
    target.parent.mkdir(parents=True, exist_ok=True)
    save_project(target, song, routes, output, workspace, xws_track_properties=xws_track_properties, midi_inputs=midi_inputs)
    return target


def read_recovery(source, directory=None):
    target = recovery_path(source, directory)
    if not target.exists():
        return None
    return load_project(target)


def discard_recovery(source, directory=None):
    target = recovery_path(source, directory)
    target.unlink(missing_ok=True)


def recovery_is_current(source, directory=None):
    """Ignore snapshots older than the last explicit save of the source."""
    backup = recovery_path(source, directory)
    if not backup.is_file():
        return False
    original = Path(source) if source else None
    return original is None or not original.exists() or backup.stat().st_mtime_ns > original.stat().st_mtime_ns


def snapshot_fingerprint(song, routes=None, output='', workspace=None, midi_inputs=None):
    """Include project settings in change detection, not only MIDI bytes."""
    from project_bundle import validate_workspace
    payload = {'routes': {str(k): str(v) for k, v in (routes or {}).items()},
               'output': str(output), 'midi_inputs': {str(k): v for k, v in (midi_inputs or {}).items()},
               'workspace': validate_workspace(workspace) if workspace is not None else None}
    digest = hashlib.sha256(song.to_bytes())
    digest.update(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8'))
    return digest.digest()
