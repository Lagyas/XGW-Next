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
    packet = midi2_note_on(group, channel, note, max(1, velocity),
                           attribute_type, attribute_data)
    if type(velocity) is not int or not 0 <= velocity <= 65535:
        raise MidiError("MIDI 2.0 release velocity out of range")
    first = (packet.words[0] & ~(0xf << 20)) | (0x8 << 20)
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
