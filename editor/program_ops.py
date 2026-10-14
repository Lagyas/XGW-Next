"""Atomic bank/program changes with deterministic ordering at a MIDI tick."""
from midi import Event, MidiError

def set_patch(song, track_index, channel, program, bank_msb=None, bank_lsb=None, tick=0):
    if type(track_index) is not int or not 0 <= track_index < len(song.tracks):
        raise MidiError('Invalid track')
    if type(channel) is not int or not 1 <= channel <= 16:
        raise MidiError('Invalid MIDI channel')
    if type(tick) is not int or not 0 <= tick <= 0x0fffffff:
        raise MidiError('Invalid MIDI tick')
    if type(program) is not int or not 0 <= program <= 127:
        raise MidiError('Invalid program')
    for value in (bank_msb, bank_lsb):
        if value is not None and (type(value) is not int or not 0 <= value <= 127):
            raise MidiError('Invalid bank')
    track = song.tracks[track_index]
    cc_status = 0xb0 | (channel - 1)
    pc_status = 0xc0 | (channel - 1)
    replacements = [(cc_status, bytes((0, bank_msb))) ] if bank_msb is not None else []
    if bank_lsb is not None:
        replacements.append((cc_status, bytes((32, bank_lsb))))
    replacements.append((pc_status, bytes((program,))))
    # Keep unrelated events; replace only matching patch setup events at this tick.
    remove = lambda e: e.tick == tick and ((e.status == pc_status) or (e.status == cc_status and len(e.data) == 2 and e.data[0] in ({0 if bank_msb is not None else -1, 32 if bank_lsb is not None else -1})))
    retained = [e for e in track.events if not remove(e)]
    order = max((e.order for e in retained), default=-1) + 1
    track.events = retained + [Event(tick, status, data, order=order + i) for i, (status, data) in enumerate(replacements)]
    song.dirty = True
    return len(replacements)
