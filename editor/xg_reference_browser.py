"""Opt-in voice/effect menus loaded from a user-supplied XGworks archive.

No original Yamaha data is shipped with XGW Next. All program numbers remain
zero-based internally; UI labels are one-based.
"""
from pathlib import Path
import zipfile
from xgworks_reference import (ReferenceFormatError, parse_model_voice_ini,
                               parse_reference_ini, hierarchical_effect_choices)

MODELS = ('MU1000', 'MU2000', 'MU128V2', 'XG', 'MU10', 'QY70', 'QY100')


def load_voice_catalog(archive_path, model='MU1000'):
    if model not in MODELS:
        raise ReferenceFormatError('Unsupported Yamaha model')
    member = 'XG4/XGEditor/' + ('XGVceList.ini' if model == 'XG' else model + '_VceList.ini')
    with zipfile.ZipFile(Path(archive_path)) as archive:
        return parse_model_voice_ini(archive.read(member))


def load_effect_catalog(archive_path, family):
    if family not in ('REVERB', 'CHORUS', 'VARIATION', 'INSERTION'):
        raise ReferenceFormatError('Unsupported effect family')
    with zipfile.ZipFile(Path(archive_path)) as archive:
        sections = parse_reference_ini(archive.read('XG4/XGEditor/EfMenu.ini'))
    return hierarchical_effect_choices(sections, family)


def find_voice(records, msb, lsb, program):
    return next((name for a, b, p, name in records
                 if (a, b, p) == (msb, lsb, program)), None)


def search_voices(records, query):
    needle = query.strip().casefold()
    return [row for row in records if needle in row[3].casefold()]
