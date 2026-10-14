"""Read-only importer for Yamaha XGworks 4 reference INI tables.

The original application and its reference data are not redistributed here.
"""
from pathlib import Path
import re
import zipfile


class ReferenceFormatError(ValueError):
    pass


def parse_reference_ini(data):
    """Return section -> indexed rows, preserving comma-delimited Yamaha values."""
    if isinstance(data, bytes):
        data = data.decode('cp932')
    if not isinstance(data, str):
        raise ReferenceFormatError('Expected INI text or bytes')
    sections = {}
    current = None
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith(';') or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            name = line[1:-1].strip()
            if not name or name in sections:
                raise ReferenceFormatError('Invalid or duplicate section')
            current = name
            sections[name] = {}
            continue
        if current is None:
            raise ReferenceFormatError('Entry outside section')
        if '=' not in line:
            raise ReferenceFormatError('Malformed INI entry')
        key, value = (part.strip() for part in line.split('=', 1))
        if re.fullmatch(r'\d+', key):
            index = int(key)
            if index in sections[current]:
                raise ReferenceFormatError('Duplicate row index')
            sections[current][index] = tuple(part.strip() for part in value.split(','))
    return sections


def load_reference_table(archive_path, member):
    """Load a named XGEditor INI from a user-provided original XG4.ZIP."""
    if not isinstance(member, str) or not re.fullmatch(r'[A-Za-z0-9_. -]+\.ini', member, re.I):
        raise ReferenceFormatError('Invalid table name')
    with zipfile.ZipFile(Path(archive_path)) as archive:
        return parse_reference_ini(archive.read('XG4/XGEditor/' + member))


def effect_choices(sections, family):
    """Return (MSB, LSB, name) for a Yamaha effect family."""
    if family not in ('REVERB', 'CHORUS', 'VARIATION'):
        raise ReferenceFormatError('Unsupported effect family')
    result = []
    for row in sections.get(family, {}).values():
        if family == 'VARIATION' and len(row) == 3 and row[0] == '1':
            continue  # Hierarchical menu group, not a concrete effect
        if len(row) < 4:
            raise ReferenceFormatError('Malformed effect entry')
        try:
            msb, lsb = int(row[1], 16), int(row[2], 16)
        except ValueError as exc:
            raise ReferenceFormatError('Invalid effect identifier') from exc
        if not (0 <= msb <= 127 and 0 <= lsb <= 127):
            raise ReferenceFormatError('Invalid effect identifier')
        result.append((msb, lsb, ','.join(row[3:])))
    return result


def hierarchical_effect_choices(sections, family, strict=False):
    """Resolve Yamaha's nested Variation/Insertion menu into concrete types.

    Return (MSB, LSB, display name), preserving the original menu order.
    Cyclic or missing menu sections are rejected rather than silently skipped.
    """
    if family not in ('REVERB', 'CHORUS', 'VARIATION', 'INSERTION'):
        raise ReferenceFormatError('Unsupported effect family')
    result = []
    def visit(section, prefix, stack):
        if section in stack:
            raise ReferenceFormatError('Cyclic effect section: ' + section)
        if section not in sections:
            if strict:
                raise ReferenceFormatError('Missing effect section: ' + section)
            return  # Original menus can reference effects defined in another file
        for row in sections[section].values():
            if len(row) >= 3 and row[0] == '1':
                visit(row[1], prefix + (row[2].lstrip('*'),), stack | {section})
            else:
                if len(row) < 4 or row[0] != '0':
                    raise ReferenceFormatError('Malformed effect menu entry')
                try:
                    msb, lsb = int(row[1], 16), int(row[2], 16)
                except ValueError as exc:
                    raise ReferenceFormatError('Invalid effect identifier') from exc
                if not (0 <= msb <= 127 and 0 <= lsb <= 127):
                    raise ReferenceFormatError('Invalid effect identifier')
                result.append((msb, lsb, ' / '.join(prefix + (','.join(row[3:]),))))
    visit(family, (), set())
    return result


def parse_model_voice_ini(data, category='Melody'):
    """Read a model voice list and return (MSB, LSB, program, label) rows."""
    if isinstance(data, bytes):
        data = data.decode('cp932')
    sections = parse_reference_ini(data)
    metadata = {}
    current = None
    for line in data.splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            current = line[1:-1].strip()
        elif current and '=' in line:
            key, value = (part.strip() for part in line.split('=', 1))
            if key == 'mode':
                try:
                    metadata[current] = tuple(int(v) for v in value.split(','))
                except ValueError as exc:
                    raise ReferenceFormatError('Invalid mode metadata') from exc
    if category not in sections or category not in metadata:
        raise ReferenceFormatError('Missing category or bank mode')
    mode = metadata[category]
    if len(mode) != 2 or not all(0 <= v <= 255 for v in mode):
        raise ReferenceFormatError('Invalid bank mode')
    # Yamaha uses 128 as a wildcard/sentinel for melodic program selection.
    msb = mode[1] if mode[0] == 128 else mode[0]
    if msb > 127:
        raise ReferenceFormatError('Invalid bank MSB')
    result = []
    for row in sections[category].values():
        if len(row) == 3:
            section = row[2]  # range start, range end, section name
        elif len(row) == 2:
            section = row[1]
        else:
            raise ReferenceFormatError('Malformed category entry')
        if section not in sections:
            raise ReferenceFormatError('Missing voice section: ' + section)
        for voice in sections[section].values():
            if len(voice) < 3:
                raise ReferenceFormatError('Malformed voice entry')
            try:
                program, lsb = int(voice[0]), int(voice[1])
            except ValueError as exc:
                raise ReferenceFormatError('Invalid voice bank/program') from exc
            if not (0 <= program <= 127 and 0 <= lsb <= 127):
                raise ReferenceFormatError('Voice bank/program out of range')
            result.append((msb, lsb, program, ','.join(voice[2:])))
    return result
