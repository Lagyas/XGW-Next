"""Conservative Yamaha XG drum and SFX kit catalog.

Program numbers are zero-based MIDI values; banks 127 and 126 use LSB 0.
Availability varies by device model.
"""
DRUM_KITS = {
    0: "Standard Kit 1", 1: "Standard Kit 2", 8: "Room Kit",
    16: "Rock Kit", 24: "Electronic Kit", 25: "Analog Kit",
    27: "Dance Kit", 32: "Jazz Kit", 40: "Brush Kit",
    48: "Symphony Kit",
}
SFX_KITS = {0: "SFX Kit 1", 1: "SFX Kit 2"}

# GM standard drum key map; kit-specific variations are not modeled yet.
GM_DRUM_NOTES = {
    35: "Acoustic Bass Drum", 36: "Bass Drum 1", 37: "Side Stick",
    38: "Acoustic Snare", 39: "Hand Clap", 40: "Electric Snare",
    41: "Low Floor Tom", 42: "Closed Hi-Hat", 43: "High Floor Tom",
    44: "Pedal Hi-Hat", 45: "Low Tom", 46: "Open Hi-Hat",
    47: "Low-Mid Tom", 48: "Hi-Mid Tom", 49: "Crash Cymbal 1",
    50: "High Tom", 51: "Ride Cymbal 1", 52: "Chinese Cymbal",
    53: "Ride Bell", 54: "Tambourine", 55: "Splash Cymbal",
    56: "Cowbell", 57: "Crash Cymbal 2", 58: "Vibraslap",
    59: "Ride Cymbal 2", 60: "Hi Bongo", 61: "Low Bongo",
    62: "Mute Hi Conga", 63: "Open Hi Conga", 64: "Low Conga",
    65: "High Timbale", 66: "Low Timbale", 67: "High Agogo",
    68: "Low Agogo", 69: "Cabasa", 70: "Maracas",
    71: "Short Whistle", 72: "Long Whistle", 73: "Short Guiro",
    74: "Long Guiro", 75: "Claves", 76: "Hi Wood Block",
    77: "Low Wood Block", 78: "Mute Cuica", 79: "Open Cuica",
    80: "Mute Triangle", 81: "Open Triangle",
}

def kit_name(msb, lsb, program):
    if not all(isinstance(v, int) and 0 <= v <= 127 for v in (msb, lsb, program)):
        raise ValueError("Bank and program must be 0..127")
    if lsb != 0:
        return None
    return {127: DRUM_KITS, 126: SFX_KITS}.get(msb, {}).get(program)

def kit_records():
    return sorted([(127, 0, p, name) for p, name in DRUM_KITS.items()] +
                  [(126, 0, p, name) for p, name in SFX_KITS.items()])
