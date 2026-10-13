"""Human-readable channel-event fields for the List Editor."""
from midi import MidiError

def event_fields(event):
    kind = event.status & 0xf0
    if not 0x80 <= event.status <= 0xef:
        raise MidiError("Only channel MIDI events have numeric fields")
    d = event.data
    if kind in (0x80, 0x90):
        return (("Note", d[0], 0, 127), ("Velocity", d[1], 0, 127))
    if kind == 0xa0:
        return (("Note", d[0], 0, 127), ("Pressure", d[1], 0, 127))
    if kind == 0xb0:
        return (("Controller", d[0], 0, 127), ("Value", d[1], 0, 127))
    if kind == 0xc0:
        return (("Program (0–127)", d[0], 0, 127),)
    if kind == 0xd0:
        return (("Channel pressure", d[0], 0, 127),)
    if kind == 0xe0:
        value = d[0] | (d[1] << 7)
        return (("Pitch bend (0–16383; center 8192)", value, 0, 16383),)
    raise MidiError("Unsupported channel event")

def encode_fields(event, values):
    fields = event_fields(event)
    if len(values) != len(fields):
        raise MidiError("Wrong number of event values")
    if any(type(value) is not int or not low <= value <= high
           for value, (_, _, low, high) in zip(values, fields)):
        raise MidiError("MIDI value out of range")
    if event.status & 0xf0 == 0xe0:
        value = values[0]
        return bytes((value & 127, (value >> 7) & 127))
    return bytes(values)
