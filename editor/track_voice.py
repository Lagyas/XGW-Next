"""Read effective channel bank/program setup from a MIDI track at a given tick.

Bank select CC0 and CC32 take effect when Program Change arrives.
This scanner does not change song events. It does not assume track == channel.
"""
from dataclasses import dataclass
from midi import MidiError

@dataclass(frozen=True)
class ChannelVoice:
    msb: int = 0
    lsb: int = 0
    program: int = 0
    has_program_change: bool = False

def channel_voice_at(song, track_index, channel, tick=0):
    if not 0 <= track_index < len(song.tracks):
        raise MidiError("Invalid track")
    if not 1 <= channel <= 16 or tick < 0:
        raise MidiError("Invalid channel or tick")
    msb, lsb, program = 0, 0, 0
    pending_msb, pending_lsb = 0, 0
    has_program = False
    events = sorted(song.tracks[track_index].events, key=lambda e: (e.tick, e.order))
    for event in events:
        if event.tick > tick:
            break
        if not 0x80 <= event.status <= 0xef or (event.status & 15) != channel - 1:
            continue
        kind = event.status & 0xf0
        if kind == 0xb0 and len(event.data) == 2:
            cc, value = event.data
            if cc == 0:
                pending_msb = value
            elif cc == 32:
                pending_lsb = value
        elif kind == 0xc0 and len(event.data) == 1:
            msb, lsb, program = pending_msb, pending_lsb, event.data[0]
            has_program = True
    return ChannelVoice(msb, lsb, program, has_program)

def used_channels(song, track_index):
    if not 0 <= track_index < len(song.tracks):
        raise MidiError("Invalid track")
    return sorted({(e.status & 15) + 1 for e in song.tracks[track_index].events
                   if 0x80 <= e.status <= 0xef})
