"""Small, conservative Yamaha XG effect type name catalog.

Only known type pairs are named. Other values remain editable as raw MSB/LSB.
Names and availability may vary by Yamaha sound module model.
"""

_EFFECT_NAMES = {
    'reverb': {
        (0, 0): 'No Effect',
        (1, 0): 'Hall 1', (1, 1): 'Hall 2',
        (2, 0): 'Room 1', (2, 1): 'Room 2', (2, 2): 'Room 3',
        (3, 0): 'Stage 1', (3, 1): 'Stage 2',
        (4, 0): 'Plate',
    },
    'chorus': {
        (0, 0): 'No Effect',
        (65, 0): 'Chorus 1', (65, 1): 'Chorus 2',
        (65, 2): 'Chorus 3', (65, 3): 'Chorus 4',
        (66, 0): 'Celeste 1', (66, 1): 'Celeste 2',
        (66, 2): 'Celeste 3', (66, 3): 'Celeste 4',
        (67, 0): 'Flanger 1', (67, 1): 'Flanger 2',
        (67, 2): 'Flanger 3',
    },
    'variation': {
        (0, 0): 'No Effect',
        (1, 0): 'Hall 1', (1, 1): 'Hall 2',
        (2, 0): 'Room 1', (2, 1): 'Room 2',
        (4, 0): 'Plate',
        (65, 0): 'Chorus 1', (65, 1): 'Chorus 2',
        (66, 0): 'Celeste 1',
        (67, 0): 'Flanger 1',
    },
}


def effect_type_name(effect, msb, lsb):
    """Human-readable name or an explicit unknown type label."""
    if effect not in _EFFECT_NAMES:
        raise ValueError('Unknown effect bus')
    for value in (msb, lsb):
        if type(value) is not int or not 0 <= value <= 127:
            raise ValueError('Effect type bytes must be 0–127 integers')
    return _EFFECT_NAMES[effect].get((msb, lsb), 'Unknown / device-specific')


def effect_type_choices(effect):
    """Sorted known presets as (msb, lsb, label) tuples."""
    if effect not in _EFFECT_NAMES:
        raise ValueError('Unknown effect bus')
    return tuple((msb, lsb, name) for (msb, lsb), name in sorted(_EFFECT_NAMES[effect].items()))
