"""Portable XGW Next project archive containing MIDI and validated sidecars."""
import io
import json
import os
from pathlib import Path
import tempfile
import zipfile

from midi import Song, MidiError
from clip_project import save_regions, load_regions, sidecar_path
from multiport_state import save_routing, load_routing

VERSION = 1
MAX_MEMBER = 64 * 1024 * 1024
MEMBERS = {'manifest.json', 'song.mid', 'song.mid.xgwclips.json', 'song.mid.xgw-routing.json', 'workspace.json', 'xws-track-properties.json'}


def save_project(path, song, routes=None, output_name='', workspace=None, xws_track_properties=None):
    path = Path(path)
    with tempfile.TemporaryDirectory() as tmp:
        midi = Path(tmp) / 'song.mid'
        midi.write_bytes(song.to_bytes())
        save_regions(midi, song)
        save_routing(midi, song, routes or {}, output_name)
        if workspace is not None:
            state = validate_workspace(workspace)
            (Path(tmp) / 'workspace.json').write_text(json.dumps(state), encoding='utf-8')
        if xws_track_properties is not None:
            from xws_track_properties import validate_track_properties
            validated = validate_track_properties(xws_track_properties, len(song.tracks))
            (Path(tmp) / 'xws-track-properties.json').write_text(json.dumps(validated), encoding='utf-8')
        manifest = json.dumps({'format': 'XGW Next', 'version': VERSION, 'midi': 'song.mid'}).encode()
        fd, staging = tempfile.mkstemp(prefix=path.name + '.', dir=str(path.parent))
        os.close(fd)
        try:
            with zipfile.ZipFile(staging, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('manifest.json', manifest)
                for member in sorted(MEMBERS - {'manifest.json'}):
                    source = Path(tmp) / member
                    if source.exists():
                        archive.write(source, member)
            os.replace(staging, path)
        finally:
            if os.path.exists(staging):
                os.unlink(staging)
    return path


def load_project(path, fallback_output=''):
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)) or not set(names) <= MEMBERS or 'manifest.json' not in names or 'song.mid' not in names:
                raise MidiError('Invalid XGW project members')
            if any(entry.file_size > MAX_MEMBER for entry in entries):
                raise MidiError('XGW project member too large')
            manifest = json.loads(archive.read('manifest.json'))
            if type(manifest) is not dict or manifest != {'format': 'XGW Next', 'version': VERSION, 'midi': 'song.mid'}:
                raise MidiError('Unsupported XGW project manifest')
            with tempfile.TemporaryDirectory() as tmp:
                for name in names:
                    (Path(tmp) / name).write_bytes(archive.read(name))
                midi = Path(tmp) / 'song.mid'
                song = Song.read(midi)
                load_regions(midi, song)
                routes = load_routing(midi, song, fallback_output)
                return song, routes
    except (zipfile.BadZipFile, KeyError, ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MidiError(f'Invalid XGW project: {exc}') from exc


def validate_workspace(state):
    """Whitelist portable editor preferences; reject malformed project UI data."""
    from workspace import WINDOW_KINDS, valid_geometry
    if type(state) is not dict or set(state) - {'geometry', 'open_editors', 'playhead_tick', 'loop_start', 'loop_end'}:
        raise MidiError('Invalid project workspace')
    geometry = state.get('geometry', {})
    editors = state.get('open_editors', [])
    if type(geometry) is not dict or type(editors) is not list:
        raise MidiError('Invalid project workspace windows')
    if any(k not in WINDOW_KINDS or not valid_geometry(v) for k, v in geometry.items()):
        raise MidiError('Invalid project window geometry')
    if len(editors) != len(set(editors)) or any(type(e) is not str or e not in WINDOW_KINDS for e in editors):
        raise MidiError('Invalid project editor list')
    result = {'geometry': geometry, 'open_editors': editors}
    for key in ('playhead_tick', 'loop_start', 'loop_end'):
        value = state.get(key, 0)
        if type(value) is not int or not 0 <= value <= 2147483647:
            raise MidiError('Invalid project timeline position')
        result[key] = value
    return result

def load_project_workspace(path):
    """Return optional UI state without changing the existing load_project API."""
    try:
        with zipfile.ZipFile(path) as archive:
            if 'workspace.json' not in archive.namelist():
                return None
            info = archive.getinfo('workspace.json')
            if info.file_size > 65536:
                raise MidiError('Project workspace too large')
            return validate_workspace(json.loads(archive.read(info)))
    except (zipfile.BadZipFile, KeyError, ValueError, UnicodeError, OSError) as exc:
        raise MidiError(f'Invalid project workspace: {exc}') from exc


def load_project_track_properties(path, track_count):
    """Read optional source channel observations without changing load_project API."""
    from xws_track_properties import validate_track_properties
    try:
        with zipfile.ZipFile(path) as archive:
            if 'xws-track-properties.json' not in archive.namelist():
                return None
            info = archive.getinfo('xws-track-properties.json')
            if info.file_size > 65536:
                raise MidiError('XWS track properties too large')
            return validate_track_properties(json.loads(archive.read(info)), track_count)
    except (zipfile.BadZipFile, KeyError, OSError, ValueError, UnicodeError) as exc:
        raise MidiError(f'Invalid XWS track properties: {exc}') from exc
