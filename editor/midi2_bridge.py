"""Explicit MIDI 1.0 channel-voice to MIDI 2.0 UMP translation.

Conversions follow the MIDI 2.0 scaling rule: repeat the source bits into
higher bits, rather than simply shifting (which would reduce the maximum).
This bridge never modifies legacy SMF events and never silently discards
unsupported MIDI messages.
"""
from midi import MidiError
from midi2_ump import (midi2_note_on, midi2_note_off,
                       midi2_control_change, midi2_pitch_bend, midi2_poly_pressure,
                       midi2_channel_pressure, midi2_program_change)


def scale_7_to_16(value):
    if type(value) is not int or not 0 <= value <= 127:
        raise MidiError("Expected 7-bit MIDI value")
    return (value << 9) | (value << 2) | (value >> 5)


def scale_7_to_32(value):
    if type(value) is not int or not 0 <= value <= 127:
        raise MidiError("Expected 7-bit MIDI value")
    return (value << 25) | (value << 18) | (value << 11) | (value << 4) | (value >> 3)


def scale_14_to_32(value):
    if type(value) is not int or not 0 <= value <= 16383:
        raise MidiError("Expected 14-bit MIDI value")
    return (value << 18) | (value << 4) | (value >> 10)


def midi1_event_to_midi2(event, group=0):
    """Convert supported SMF channel events into a MIDI 2.0 UMP packet.

    This is an explicit, lossy *protocol translation*, not a conversion of
    SMF files into a MIDI 2.0 file format. MIDI 1.0 Note On velocity zero
    becomes a MIDI 2.0 Note Off with zero release velocity.
    """
    if type(group) is not int or not 0 <= group <= 15:
        raise MidiError("UMP group must be 0–15")
    status = event.status
    if not 0x80 <= status <= 0xef:
        raise MidiError("Only MIDI 1.0 channel events can be translated")
    kind = status & 0xf0
    channel = status & 15
    data = event.data
    expected = 1 if kind in (0xc0, 0xd0) else 2
    if len(data) != expected or any(type(v) is not int or v > 127 for v in data):
        raise MidiError("Malformed MIDI 1.0 channel event")
    if kind == 0x80 or (kind == 0x90 and data[1] == 0):
        return midi2_note_off(group, channel, data[0], scale_7_to_16(data[1]))
    if kind == 0x90:
        return midi2_note_on(group, channel, data[0], scale_7_to_16(data[1]))
    if kind == 0xa0:
        return midi2_poly_pressure(group, channel, data[0], scale_7_to_32(data[1]))
    if kind == 0xc0:
        return midi2_program_change(group, channel, data[0])
    if kind == 0xd0:
        return midi2_channel_pressure(group, channel, scale_7_to_32(data[0]))
    if kind == 0xb0:
        return midi2_control_change(group, channel, data[0], scale_7_to_32(data[1]))
    if kind == 0xe0:
        return midi2_pitch_bend(group, channel, scale_14_to_32(data[0] | (data[1] << 7)))
    raise MidiError("Unsupported MIDI 1.0 channel event")
