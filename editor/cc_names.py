"""Standard MIDI 1.0 Control Change labels for the Piano Roll controller lane.

Undefined controller numbers are intentionally shown as undefined; hardware
may assign vendor-specific meanings to them.
"""
CC_NAMES = {
    0: "Bank Select MSB", 1: "Modulation Wheel MSB", 2: "Breath Controller MSB",
    4: "Foot Controller MSB", 5: "Portamento Time MSB",
    6: "Data Entry MSB", 7: "Channel Volume MSB", 8: "Balance MSB",
    10: "Pan MSB", 11: "Expression Controller MSB",
    12: "Effect Control 1 MSB", 13: "Effect Control 2 MSB",
    16: "General Purpose Controller 1 MSB", 17: "General Purpose Controller 2 MSB",
    18: "General Purpose Controller 3 MSB", 19: "General Purpose Controller 4 MSB",
    32: "Bank Select LSB", 33: "Modulation Wheel LSB", 34: "Breath Controller LSB",
    36: "Foot Controller LSB", 37: "Portamento Time LSB",
    38: "Data Entry LSB", 39: "Channel Volume LSB", 40: "Balance LSB",
    42: "Pan LSB", 43: "Expression Controller LSB",
    44: "Effect Control 1 LSB", 45: "Effect Control 2 LSB",
    48: "General Purpose Controller 1 LSB", 49: "General Purpose Controller 2 LSB",
    50: "General Purpose Controller 3 LSB", 51: "General Purpose Controller 4 LSB",
    64: "Damper Pedal (Sustain)", 65: "Portamento On/Off",
    66: "Sostenuto", 67: "Soft Pedal", 68: "Legato Footswitch",
    69: "Hold 2", 70: "Sound Controller 1 (Sound Variation)",
    71: "Sound Controller 2 (Timbre / Resonance)",
    72: "Sound Controller 3 (Release Time)",
    73: "Sound Controller 4 (Attack Time)",
    74: "Sound Controller 5 (Brightness / Cutoff)",
    75: "Sound Controller 6 (Decay Time)",
    76: "Sound Controller 7 (Vibrato Rate)",
    77: "Sound Controller 8 (Vibrato Depth)",
    78: "Sound Controller 9 (Vibrato Delay)",
    79: "Sound Controller 10",
    80: "General Purpose Controller 5",
    81: "General Purpose Controller 6",
    82: "General Purpose Controller 7",
    83: "General Purpose Controller 8",
    84: "Portamento Control",
    88: "High Resolution Velocity Prefix",
    91: "Effects 1 Depth (Reverb Send)",
    92: "Effects 2 Depth (Tremolo)",
    93: "Effects 3 Depth (Chorus Send)",
    94: "Effects 4 Depth (Celeste / Detune)",
    95: "Effects 5 Depth (Phaser)",
    96: "Data Increment", 97: "Data Decrement",
    98: "NRPN LSB", 99: "NRPN MSB",
    100: "RPN LSB", 101: "RPN MSB",
    120: "All Sound Off", 121: "Reset All Controllers",
    122: "Local Control On/Off", 123: "All Notes Off",
    124: "Omni Mode Off", 125: "Omni Mode On",
    126: "Mono Mode On", 127: "Poly Mode On",
}


def cc_label(number):
    """Return a readable controller label, including its MIDI CC number."""
    if type(number) is not int or not 0 <= number <= 127:
        raise ValueError("MIDI CC number must be an integer from 0 to 127")
    return f"CC {number:03d} – {CC_NAMES.get(number, 'Undefined / device-specific')}"
