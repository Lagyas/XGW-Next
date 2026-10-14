"""Persist user preferences outside MIDI song files."""
import json
import os
from pathlib import Path


def settings_path():
    base = os.environ.get('APPDATA')
    return (Path(base) / 'XGW Next' / 'settings.json' if base
            else Path.home() / '.config' / 'xgw-next' / 'settings.json')


def load_settings(path=None):
    target = Path(path) if path is not None else settings_path()
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}


def save_settings(settings, path=None):
    target = Path(path) if path is not None else settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(target)
