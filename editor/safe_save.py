"""Crash-resistant file replacement for MIDI project data.

Writes and fsyncs a temporary file before replacing the destination. When
replacing an existing file, keeps its previous contents in a .bak sibling.
"""
import os
from pathlib import Path
import shutil
import tempfile


def atomic_write(path, data, *, backup=True):
    path = Path(path)
    if not isinstance(data, bytes):
        raise TypeError('Expected bytes')
    fd, temp = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if backup and path.exists():
            backup_path = path.with_name(path.name + '.bak')
            backup_fd, backup_temp = tempfile.mkstemp(prefix='.' + path.name + '.backup.', dir=path.parent)
            try:
                with os.fdopen(backup_fd, 'wb') as dest, path.open('rb') as source:
                    shutil.copyfileobj(source, dest)
                    dest.flush()
                    os.fsync(dest.fileno())
                os.replace(backup_temp, backup_path)
            finally:
                if os.path.exists(backup_temp):
                    os.unlink(backup_temp)
        os.replace(temp, path)
        if os.name != 'nt':
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
