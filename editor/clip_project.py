"""Versioned sidecar for explicit clip regions, separate from standard MIDI data.

The SHA-256 binding prevents stale regions being applied to a different MIDI file.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4
from arrangement import track_clips
from midi import MidiError

VERSION = 2


def sidecar_path(midi_path):
    return Path(str(midi_path) + '.xgwclips.json')


def save_regions(midi_path, song):
    midi_path = Path(midi_path)
    target = sidecar_path(midi_path)
    tracks = []
    for track in song.tracks:
        regions = getattr(track, 'clip_regions', None)
        tracks.append(None if regions is None else [list(r) for r in regions])
    if all(r is None for r in tracks) and not any(t.events for t in song.tracks):
        if target.exists():
            target.unlink()
        return None
    identities = []
    for track in song.tracks:
        regions = getattr(track, 'clip_regions', None)
        if regions is not None:
            ids = getattr(track, 'clip_region_ids', None)
            if not isinstance(ids, list) or len(ids) != len(regions) or len(set(ids)) != len(ids):
                ids = [uuid4().hex for _ in regions]
                track.clip_region_ids = ids
        else:
            ids = None
        identities.append({'events': [e.uid for e in track.events], 'clips': ids})
    payload = {'identities': identities, 'version': VERSION, 'midi_sha256': hashlib.sha256(midi_path.read_bytes()).hexdigest(),
               'division': song.division, 'tracks': tracks}
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
    fd, temporary = tempfile.mkstemp(prefix=target.name + '.', dir=str(target.parent))
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def load_regions(midi_path, song):
    """Validate the entire sidecar before mutating any track."""
    path = sidecar_path(midi_path)
    if not path.exists():
        return False
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
        if type(obj) is not dict or obj.get('version') not in (1, VERSION):
            raise ValueError('Unsupported clip project version')
        if obj.get('midi_sha256') != hashlib.sha256(Path(midi_path).read_bytes()).hexdigest():
            raise ValueError('Clip project does not match MIDI file')
        if obj.get('division') != song.division:
            raise ValueError('MIDI timing does not match clip project')
        entries = obj.get('tracks')
        if type(entries) is not list or len(entries) != len(song.tracks):
            raise ValueError('Clip project track count mismatch')
        identity_entries = obj.get('identities') if obj.get('version') == VERSION else None
        if identity_entries is not None:
            if type(identity_entries) is not list or len(identity_entries) != len(song.tracks):
                raise ValueError('Invalid identity track count')
        checked = []
        for entry in entries:
            if entry is None:
                checked.append(None)
                continue
            if type(entry) is not list:
                raise ValueError('Invalid clip region list')
            last_end = -1
            result = []
            for pair in entry:
                if (type(pair) is not list or len(pair) != 2 or
                    any(type(v) is not int for v in pair)):
                    raise ValueError('Invalid clip region coordinates')
                start, end = pair
                if start < 0 or end <= start or start < last_end:
                    raise ValueError('Overlapping or invalid clip regions')
                result.append((start, end))
                last_end = end
            checked.append(result)
        validated_ids = []
        seen = set()
        for i, track in enumerate(song.tracks):
            entry = identity_entries[i] if identity_entries is not None else None
            if entry is None:
                validated_ids.append((None, None))
                continue
            if type(entry) is not dict:
                raise ValueError('Invalid identity record')
            event_ids, clip_ids = entry.get('events'), entry.get('clips')
            if type(event_ids) is not list or len(event_ids) != len(track.events):
                raise ValueError('MIDI event identity count mismatch')
            if clip_ids is not None and (type(clip_ids) is not list or checked[i] is None or len(clip_ids) != len(checked[i])):
                raise ValueError('Clip identity count mismatch')
            for uid in event_ids + (clip_ids or []):
                if type(uid) is not str or len(uid) != 32 or any(c not in '0123456789abcdef' for c in uid) or uid in seen:
                    raise ValueError('Duplicate or invalid identity')
                seen.add(uid)
            validated_ids.append((event_ids, clip_ids))
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        raise MidiError(f'Cannot load clip regions: {exc}') from exc
    for track, regions, ids in zip(song.tracks, checked, validated_ids):
        event_ids, clip_ids = ids
        if event_ids is not None:
            for event, uid in zip(track.events, event_ids):
                event.uid = uid
        if clip_ids is not None:
            track.clip_region_ids = list(clip_ids)
        elif hasattr(track, 'clip_region_ids'):
            del track.clip_region_ids
        if regions is None:
            if hasattr(track, 'clip_regions'):
                del track.clip_regions
        else:
            track.clip_regions = regions
    return True
