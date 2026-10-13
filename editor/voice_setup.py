"""Write a selected XG Part's voice settings into a MIDI track.

Inserts standard Bank Select MSB/LSB + Program Change at tick zero.
This is channel-level MIDI, not an XG Part SysEx block; channel-to-Part
routing must be confirmed by the user. Existing messages are preserved.
"""
from midi import Event, MidiError

def insert_voice_setup(song, track_index, channel, msb, lsb, program):
    if not 0 <= track_index < len(song.tracks):
        raise MidiError("Invalid track")
    if not 1 <= channel <= 16:
        raise MidiError("Channel must be 1..16")
    if any(not isinstance(v, int) or not 0 <= v <= 127 for v in (msb, lsb, program)):
        raise MidiError("Bank/program must be 0..127")
    track = song.tracks[track_index]
    ch = channel - 1
    # Place setup before existing tick-zero channel events.
    first_order = min((e.order for e in track.events if e.tick == 0), default=0)
    for e in track.events:
        if e.tick == 0:
            e.order += 3
    track.events.extend([
        Event(0, 0xb0 | ch, bytes((0, msb)), order=first_order),
        Event(0, 0xb0 | ch, bytes((32, lsb)), order=first_order + 1),
        Event(0, 0xc0 | ch, bytes((program,)), order=first_order + 2),
    ])
    song.dirty = True
    return 3
