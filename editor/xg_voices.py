"""Small, explicitly curated XG voice catalog.

GM/XG bank 0 names are generic GM instrument names. XG variations are
device-dependent; unknown combinations are never silently claimed supported.
MIDI program is zero-based; human-readable display is one-based.
"""
GM_NAMES = (
"Acoustic Grand Piano","Bright Acoustic Piano","Electric Grand Piano","Honky-tonk Piano",
"Electric Piano 1","Electric Piano 2","Harpsichord","Clavi",
"Celesta","Glockenspiel","Music Box","Vibraphone","Marimba","Xylophone","Tubular Bells","Dulcimer",
"Drawbar Organ","Percussive Organ","Rock Organ","Church Organ","Reed Organ","Accordion","Harmonica","Tango Accordion",
"Acoustic Guitar (nylon)","Acoustic Guitar (steel)","Electric Guitar (jazz)","Electric Guitar (clean)",
"Electric Guitar (muted)","Overdriven Guitar","Distortion Guitar","Guitar Harmonics",
"Acoustic Bass","Electric Bass (finger)","Electric Bass (pick)","Fretless Bass","Slap Bass 1","Slap Bass 2","Synth Bass 1","Synth Bass 2",
"Violin","Viola","Cello","Contrabass","Tremolo Strings","Pizzicato Strings","Orchestral Harp","Timpani",
"String Ensemble 1","String Ensemble 2","SynthStrings 1","SynthStrings 2","Choir Aahs","Voice Oohs","Synth Voice","Orchestra Hit",
"Trumpet","Trombone","Tuba","Muted Trumpet","French Horn","Brass Section","SynthBrass 1","SynthBrass 2",
"Soprano Sax","Alto Sax","Tenor Sax","Baritone Sax","Oboe","English Horn","Bassoon","Clarinet",
"Piccolo","Flute","Recorder","Pan Flute","Blown Bottle","Shakuhachi","Whistle","Ocarina",
"Lead 1 (square)","Lead 2 (sawtooth)","Lead 3 (calliope)","Lead 4 (chiff)","Lead 5 (charang)","Lead 6 (voice)","Lead 7 (fifths)","Lead 8 (bass + lead)",
"Pad 1 (new age)","Pad 2 (warm)","Pad 3 (polysynth)","Pad 4 (choir)","Pad 5 (bowed)","Pad 6 (metallic)","Pad 7 (halo)","Pad 8 (sweep)",
"FX 1 (rain)","FX 2 (soundtrack)","FX 3 (crystal)","FX 4 (atmosphere)","FX 5 (brightness)","FX 6 (goblins)","FX 7 (echoes)","FX 8 (sci-fi)",
"Sitar","Banjo","Shamisen","Koto","Kalimba","Bag Pipe","Fiddle","Shanai",
"Tinkle Bell","Agogo","Steel Drums","Woodblock","Taiko Drum","Melodic Tom","Synth Drum","Reverse Cymbal",
"Guitar Fret Noise","Breath Noise","Seashore","Bird Tweet","Telephone Ring","Helicopter","Applause","Gunshot",
)
assert len(GM_NAMES) == 128

# Selected XG variations, keyed (bank MSB, bank LSB, MIDI program 0..127).
# The table is deliberately small rather than guessing at unsupported banks.
XG_VARIATIONS = {
    (0, 1, 0): "Grand Piano KSP",
    (0, 18, 0): "Mellow Grand Piano",
    (0, 40, 0): "Piano Strings",
    (0, 41, 0): "Dream",
    (0, 1, 1): "Bright Piano KSP",
    (0, 1, 2): "Electric Grand Piano KSP",
    (0, 32, 2): "Detuned CP80",
    (0, 40, 2): "Layered CP 1",
    (0, 41, 2): "Layered CP 2",
    (0, 1, 4): "Electric Piano 1 KSP",
    (0, 18, 4): "Mellow Electric Piano 1",
    (0, 32, 4): "Chorus Electric Piano 1",
    (0, 40, 4): "Hard Electric Piano",
    (0, 64, 4): "60s Electric Piano 1",
    (0, 18, 33): "Finger Bass Dark",
    (0, 40, 32): "Jazz Rhythm",
}

def voice_name(msb, lsb, program):
    """Return known name or None; never assume a variation exists."""
    if not all(isinstance(v, int) and 0 <= v <= 127 for v in (msb, lsb, program)):
        raise ValueError("MIDI bank and program values must be 0..127")
    if msb == 0 and lsb == 0:
        return GM_NAMES[program]
    return XG_VARIATIONS.get((msb, lsb, program))

def voice_label(msb, lsb, program):
    name = voice_name(msb, lsb, program)
    return name if name is not None else f"Unknown voice (MSB {msb}, LSB {lsb}, Program {program+1})"

def matching_voices(search="", msb=None, lsb=None):
    """Return sorted (msb, lsb, program, name) tuples for curated voices."""
    records = [(0, 0, i, name) for i, name in enumerate(GM_NAMES)]
    records += [(a, b, p, name) for (a, b, p), name in XG_VARIATIONS.items()]
    term = search.casefold().strip()
    return sorted((a, b, p, name) for a, b, p, name in records
                  if (msb is None or msb == a) and (lsb is None or lsb == b)
                  and (not term or term in name.casefold()))
