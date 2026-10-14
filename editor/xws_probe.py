"""Read-only inspection of legacy XGworks projects; no guessed XWS parser.

XWS is not SMF. Only report validated embedded SMF headers as candidates;
never treat byte patterns as proof of a recoverable project.
"""
from dataclasses import dataclass
from pathlib import Path
import struct

MAX_SCAN = 32 * 1024 * 1024
MAX_CANDIDATES = 32


@dataclass(frozen=True)
class SmfCandidate:
    offset: int
    format: int
    tracks: int
    division: int


@dataclass(frozen=True)
class XwsReport:
    size: int
    signature_hex: str
    embedded_midi: tuple
    truncated_scan: bool


def inspect_xws(path):
    """Inspect without modifying the source or interpreting undocumented chunks."""
    path = Path(path)
    with path.open('rb') as stream:
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(0)
        data = stream.read(MAX_SCAN)
    found = []
    cursor = 0
    while len(found) < MAX_CANDIDATES:
        offset = data.find(b'MThd', cursor)
        if offset < 0:
            break
        cursor = offset + 4
        if offset + 14 > len(data):
            continue
        length, fmt, tracks, division = struct.unpack_from('>IHHH', data, offset + 4)
        if length != 6 or fmt > 2 or not 1 <= tracks <= 65535 or not 1 <= division <= 0xffff:
            continue
        # A valid SMF begins with a track chunk immediately after its header.
        if data[offset + 14:offset + 18] != b'MTrk':
            continue
        if offset + 22 > len(data):
            continue
        track_length = struct.unpack_from('>I', data, offset + 18)[0]
        if track_length > len(data) - (offset + 22):
            continue
        found.append(SmfCandidate(offset, fmt, tracks, division))
    return XwsReport(size, data[:16].hex(' '), tuple(found), size > MAX_SCAN)


def format_report(report):
    lines = [f'File size: {report.size:,} bytes', f'First 16 bytes: {report.signature_hex}',
             f'Validated embedded MIDI headers: {len(report.embedded_midi)}']
    for item in report.embedded_midi:
        lines.append(f'  Offset {item.offset}: SMF format {item.format}, {item.tracks} tracks, division {item.division}')
    if report.truncated_scan:
        lines.append('Only the first 32 MiB were inspected.')
    lines.append('XWS import is not available yet: a real sample is needed to verify the proprietary structure.')
    return '\n'.join(lines)


def extract_embedded_smf(path, offset):
    """Return a complete, parser-validated SMF embedded at a known byte offset.

    This is MIDI salvage, NOT import of XGworks project structure.
    """
    from midi import Song, MidiError
    if type(offset) is not int or offset < 0:
        raise ValueError('Invalid MIDI offset')
    with Path(path).open('rb') as stream:
        stream.seek(0, 2)
        total = stream.tell()
        if offset > total or total - offset < 14:
            raise MidiError('Missing embedded MIDI header')
        stream.seek(offset)
        header = stream.read(14)
        if header[:8] != b'MThd\x00\x00\x00\x06':
            raise MidiError('Unsupported embedded MIDI header')
        fmt, tracks, division = struct.unpack('>HHH', header[8:14])
        if fmt > 2 or not 1 <= tracks <= 65535 or not division:
            raise MidiError('Invalid embedded MIDI header')
        data = bytearray(header)
        # Only accept consecutive MTrk chunks; never consume surrounding XWS data.
        # Limit total memory and prevent hostile track-count/size declarations.
        if tracks > 1024:
            raise MidiError('Too many embedded MIDI tracks')
        for _ in range(tracks):
            chunk = stream.read(8)
            if len(chunk) != 8 or chunk[:4] != b'MTrk':
                raise MidiError('Incomplete embedded MIDI track list')
            length = struct.unpack('>I', chunk[4:])[0]
            if length > MAX_SCAN or len(data) + 8 + length > MAX_SCAN:
                raise MidiError('Embedded MIDI exceeds safe extraction limit')
            body = stream.read(length)
            if len(body) != length:
                raise MidiError('Truncated embedded MIDI track')
            data.extend(chunk)
            data.extend(body)
    result = bytes(data)
    Song.from_bytes(result)  # validate all event streams, not only chunk headers
    return result
