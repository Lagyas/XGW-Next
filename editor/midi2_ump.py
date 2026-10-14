"""MIDI 2.0 Universal MIDI Packet foundations.

UMP packets are 32-bit aligned and are not SMF 1.0 track events. Keep them
separate from legacy MIDI Event objects to avoid silently truncating MIDI 2.0
values. This module validates and decodes MIDI 2.0 channel-voice packets.
"""
from dataclasses import dataclass
from midi import MidiError

# UMP message type -> number of 32-bit words.
UMP_WORD_COUNTS = (1, 1, 1, 2, 2, 4, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4)

@dataclass(frozen=True)
class UmpPacket:
    words: tuple[int, ...]

    def __post_init__(self):
        if not self.words or any(type(w) is not int or not 0 <= w <= 0xffffffff
                                 for w in self.words):
            raise MidiError("UMP words must be unsigned 32-bit integers")
        expected = UMP_WORD_COUNTS[self.message_type]
        if len(self.words) != expected:
            raise MidiError(f"UMP message type {self.message_type:X} requires {expected} words")

    @property
    def message_type(self):
        return (self.words[0] >> 28) & 0xf

    @property
    def group(self):
        return (self.words[0] >> 24) & 0xf

    def to_bytes(self):
        return b"".join(word.to_bytes(4, "big") for word in self.words)

    @classmethod
    def from_bytes(cls, data):
        if len(data) < 4 or len(data) % 4:
            raise MidiError("UMP data must be 32-bit aligned")
        words = tuple(int.from_bytes(data[i:i+4], "big")
                      for i in range(0, len(data), 4))
        return cls(words)

    def midi2_channel_voice(self):
        if self.message_type != 0x4:
            raise MidiError("Not a MIDI 2.0 Channel Voice packet")
        first, second = self.words
        status = (first >> 20) & 0xf
        channel = (first >> 16) & 0xf
        index = (first >> 8) & 0xff
        attribute_type = first & 0xff
        return {
            "group": self.group,
            "status": status,
            "channel": channel,
            "index": index,
            "attribute_type": attribute_type,
            "data32": second,
        }


def midi2_note_on(group, channel, note, velocity, attribute_type=0, attribute_data=0):
    """Construct MIDI 2.0 Note On (status 9), 16-bit velocity and attribute."""
    if any(type(v) is not int for v in
           (group, channel, note, velocity, attribute_type, attribute_data)):
        raise MidiError("MIDI 2.0 note fields must be integers")
    if not (0 <= group <= 15 and 0 <= channel <= 15 and
            0 <= note <= 127 and 1 <= velocity <= 65535 and
            0 <= attribute_type <= 255 and 0 <= attribute_data <= 65535):
        raise MidiError("MIDI 2.0 note field out of range")
    first = (0x4 << 28) | (group << 24) | (0x9 << 20) | (channel << 16) | (note << 8) | attribute_type
    second = (velocity << 16) | attribute_data
    return UmpPacket((first, second))

def midi2_note_off(group, channel, note, velocity=0, attribute_type=0, attribute_data=0):
    """Construct MIDI 2.0 Note Off (status 8), preserving 16-bit release velocity."""
    if any(type(v) is not int for v in
           (group, channel, note, velocity, attribute_type, attribute_data)):
        raise MidiError("MIDI 2.0 note fields must be integers")
    if not (0 <= group <= 15 and 0 <= channel <= 15 and
            0 <= note <= 127 and 0 <= velocity <= 65535 and
            0 <= attribute_type <= 255 and 0 <= attribute_data <= 65535):
        raise MidiError("MIDI 2.0 note field out of range")
    first = (0x4 << 28) | (group << 24) | (0x8 << 20) | (channel << 16) | (note << 8) | attribute_type
    return UmpPacket((first, (velocity << 16) | attribute_data))


def midi2_control_change(group, channel, controller, value):
    """Construct MIDI 2.0 Control Change with full unsigned 32-bit resolution."""
    if any(type(v) is not int for v in (group, channel, controller, value)):
        raise MidiError("MIDI 2.0 controller fields must be integers")
    if not (0 <= group <= 15 and 0 <= channel <= 15 and
            0 <= controller <= 127 and 0 <= value <= 0xffffffff):
        raise MidiError("MIDI 2.0 controller field out of range")
    first = (0x4 << 28) | (group << 24) | (0xb << 20) | (channel << 16) | (controller << 8)
    return UmpPacket((first, value))



def midi2_pitch_bend(group, channel, value):
    """MIDI 2.0 channel pitch bend: unsigned 32-bit, center 0x80000000."""
    if any(type(v) is not int for v in (group, channel, value)):
        raise MidiError("MIDI 2.0 pitch bend fields must be integers")
    if not (0 <= group <= 15 and 0 <= channel <= 15 and
            0 <= value <= 0xffffffff):
        raise MidiError("MIDI 2.0 pitch bend field out of range")
    first = (0x4 << 28) | (group << 24) | (0xe << 20) | (channel << 16)
    return UmpPacket((first, value))


def midi2_per_note_pitch_bend(group, channel, note, value):
    """MIDI 2.0 per-note pitch bend (status 6), with 32-bit bend value."""
    if any(type(v) is not int for v in (group, channel, note, value)):
        raise MidiError("MIDI 2.0 per-note pitch bend fields must be integers")
    if not (0 <= group <= 15 and 0 <= channel <= 15 and
            0 <= note <= 127 and 0 <= value <= 0xffffffff):
        raise MidiError("MIDI 2.0 per-note pitch bend field out of range")
    first = (0x4 << 28) | (group << 24) | (0x6 << 20) | (channel << 16) | (note << 8)
    return UmpPacket((first, value))

def midi2_poly_pressure(group, channel, note, value):
    """MIDI 2.0 Polyphonic Key Pressure with 32-bit pressure."""
    if any(type(v) is not int for v in (group, channel, note, value)):
        raise MidiError("MIDI 2.0 poly pressure fields must be integers")
    if not (0 <= group <= 15 and 0 <= channel <= 15 and
            0 <= note <= 127 and 0 <= value <= 0xffffffff):
        raise MidiError("MIDI 2.0 poly pressure field out of range")
    first = (4 << 28) | (group << 24) | (0xa << 20) | (channel << 16) | (note << 8)
    return UmpPacket((first, value))


def midi2_channel_pressure(group, channel, value):
    """MIDI 2.0 Channel Pressure with 32-bit pressure."""
    if any(type(v) is not int for v in (group, channel, value)):
        raise MidiError("MIDI 2.0 channel pressure fields must be integers")
    if not (0 <= group <= 15 and 0 <= channel <= 15 and 0 <= value <= 0xffffffff):
        raise MidiError("MIDI 2.0 channel pressure field out of range")
    first = (4 << 28) | (group << 24) | (0xd << 20) | (channel << 16)
    return UmpPacket((first, value))


def midi2_program_change(group, channel, program):
    """MIDI 2.0 Program Change without optional bank fields."""
    if any(type(v) is not int for v in (group, channel, program)):
        raise MidiError("MIDI 2.0 program fields must be integers")
    if not (0 <= group <= 15 and 0 <= channel <= 15 and 0 <= program <= 127):
        raise MidiError("MIDI 2.0 program field out of range")
    first = (4 << 28) | (group << 24) | (0xc << 20) | (channel << 16)
    return UmpPacket((first, program << 24))


def unpack_ump_stream(data):
    """Decode consecutive UMP packets without discarding message boundaries."""
    if len(data) % 4:
        raise MidiError("Truncated UMP stream")
    packets = []
    pos = 0
    while pos < len(data):
        first = int.from_bytes(data[pos:pos + 4], "big")
        size = UMP_WORD_COUNTS[(first >> 28) & 0xf] * 4
        if pos + size > len(data):
            raise MidiError("Truncated UMP packet")
        packets.append(UmpPacket.from_bytes(data[pos:pos + size]))
        pos += size
    return packets
