"""Timed MIDI 2.0 channel events, independent of legacy SMF tracks.

This is an in-memory editing model, not a MIDI 2.0 file format or a
transport. It preserves UMP precision and opaque packets without downcasting.
"""
from dataclasses import dataclass, field
from midi import MidiError
from midi2_ump import UmpPacket, midi2_note_on, midi2_note_off

MAX_TICK = 0x0fffffff


@dataclass(frozen=True)
class TimedUmpEvent:
    tick: int
    packet: UmpPacket

    def __post_init__(self):
        if type(self.tick) is not int or not 0 <= self.tick <= MAX_TICK:
            raise MidiError("MIDI event tick outside supported range")
        if not isinstance(self.packet, UmpPacket):
            raise MidiError("Timed MIDI 2.0 event requires a UMP packet")


@dataclass(frozen=True)
class Midi2Note:
    on_index: int
    off_index: int
    start: int
    end: int
    group: int
    channel: int
    pitch: int
    velocity: int
    release_velocity: int
    on_attribute_type: int
    on_attribute_data: int
    off_attribute_type: int
    off_attribute_data: int


def _note_fields(event):
    packet = event.packet
    if packet.message_type != 4:
        return None
    fields = packet.midi2_channel_voice()
    if fields["status"] not in (8, 9):
        return None
    return fields


@dataclass
class Midi2Sequence:
    """Sequence of timed UMP events; event indices are stable until editing."""
    events: list[TimedUmpEvent] = field(default_factory=list)
    dirty: bool = False

    def __post_init__(self):
        if any(not isinstance(event, TimedUmpEvent) for event in self.events):
            raise MidiError("Sequence contains an invalid timed UMP event")

    def notes(self):
        """Pair Note On/Off by group, channel, pitch (FIFO for overlaps)."""
        from collections import defaultdict, deque
        pending = defaultdict(deque)
        result = []
        for index, event in sorted(enumerate(self.events),
                                   key=lambda item: (item[1].tick, item[0])):
            fields = _note_fields(event)
            if fields is None:
                continue
            key = (fields["group"], fields["channel"], fields["index"])
            if fields["status"] == 9:
                pending[key].append((index, event, fields))
            elif pending[key]:
                on_index, on, on_fields = pending[key].popleft()
                result.append(Midi2Note(
                    on_index, index, on.tick, event.tick, *key,
                    on_fields["data32"] >> 16, fields["data32"] >> 16,
                    on_fields["attribute_type"], on_fields["data32"] & 0xffff,
                    fields["attribute_type"], fields["data32"] & 0xffff))
        return result

    def insert_note(self, start, end, group, channel, pitch, velocity,
                    release_velocity=0, attribute_type=0, attribute_data=0):
        if (type(start) is not int or type(end) is not int or
                not 0 <= start < end <= MAX_TICK):
            raise MidiError("MIDI 2.0 note must have positive duration")
        on = midi2_note_on(group, channel, pitch, velocity,
                           attribute_type, attribute_data)
        off = midi2_note_off(group, channel, pitch, release_velocity)
        self.events.extend((TimedUmpEvent(start, on), TimedUmpEvent(end, off)))
        self.dirty = True
        return (len(self.events) - 2, len(self.events) - 1)

    def edit_note(self, on_index, off_index, *, start=None, end=None,
                  pitch=None, velocity=None, release_velocity=None):
        """Edit a paired note atomically, preserving UMP note attributes."""
        note = next((n for n in self.notes()
                     if (n.on_index, n.off_index) == (on_index, off_index)), None)
        if note is None:
            raise MidiError("Selected MIDI 2.0 note pair is invalid")
        start = note.start if start is None else start
        end = note.end if end is None else end
        pitch = note.pitch if pitch is None else pitch
        velocity = note.velocity if velocity is None else velocity
        release_velocity = note.release_velocity if release_velocity is None else release_velocity
        if (type(start) is not int or type(end) is not int or
                not 0 <= start < end <= MAX_TICK):
            raise MidiError("MIDI 2.0 note must have positive duration")
        on = midi2_note_on(note.group, note.channel, pitch, velocity,
                           note.on_attribute_type, note.on_attribute_data)
        off = midi2_note_off(note.group, note.channel, pitch, release_velocity,
                             note.off_attribute_type, note.off_attribute_data)
        changed = (start != note.start or end != note.end or
                   on != self.events[on_index].packet or
                   off != self.events[off_index].packet)
        if changed:
            # Check FIFO note matching after the edit. Overlapping notes of the
            # same pitch/channel can otherwise silently change their partners.
            proposed = list(self.events)
            proposed[on_index] = TimedUmpEvent(start, on)
            proposed[off_index] = TimedUmpEvent(end, off)
            candidate = Midi2Sequence(proposed)
            if not any((n.on_index, n.off_index) == (on_index, off_index)
                       for n in candidate.notes()):
                raise MidiError("Edit would change MIDI 2.0 note pairing")
            self.events[:] = proposed
            self.dirty = True
        return changed

    def delete_note(self, on_index, off_index):
        if not any((n.on_index, n.off_index) == (on_index, off_index)
                   for n in self.notes()):
            raise MidiError("Selected MIDI 2.0 note pair is invalid")
        for index in sorted((on_index, off_index), reverse=True):
            del self.events[index]
        self.dirty = True


def quantize_midi2_notes(sequence, pairs, grid, strength=100):
    """Quantize selected MIDI 2.0 note starts while preserving note duration.

    All changes are validated before any event is modified.
    """
    if not isinstance(sequence, Midi2Sequence):
        raise MidiError("Expected MIDI 2.0 sequence")
    if (type(grid) is not int or grid < 1 or
            type(strength) is not int or not 0 <= strength <= 100):
        raise MidiError("Invalid MIDI 2.0 quantization settings")
    valid = {(n.on_index, n.off_index): n for n in sequence.notes()}
    selected = list(dict.fromkeys(tuple(pair) for pair in pairs))
    if any(pair not in valid for pair in selected):
        raise MidiError("Invalid MIDI 2.0 note selection")
    changes = []
    for pair in selected:
        note = valid[pair]
        target = ((note.start + grid // 2) // grid) * grid
        delta = round((target - note.start) * strength / 100)
        if not 0 <= note.start + delta < note.end + delta <= MAX_TICK:
            raise MidiError("Quantized MIDI 2.0 note exceeds timeline limits")
        if delta:
            changes.append((note, delta))
    for note, delta in changes:
        sequence.events[note.on_index] = TimedUmpEvent(
            note.start + delta, sequence.events[note.on_index].packet)
        sequence.events[note.off_index] = TimedUmpEvent(
            note.end + delta, sequence.events[note.off_index].packet)
    if changes:
        sequence.dirty = True
    return len(changes)


def import_midi1_track(track, group=0):
    """Translate only SMF channel events into a timed MIDI 2.0 sequence.

    Meta and SysEx are *not* representable as channel voice UMP. Reject them
    instead of silently losing tempo, lyrics, XG SysEx, or other information.
    Use channel_events_only=True explicitly to request channel-only import.
    """
    return _import_midi1_track(track, group, channel_events_only=False)


def import_midi1_channel_events(track, group=0):
    """Explicitly import channel events, intentionally excluding meta/SysEx."""
    return _import_midi1_track(track, group, channel_events_only=True)


def _import_midi1_track(track, group, channel_events_only):
    from midi2_bridge import midi1_event_to_midi2
    events = []
    for event in track.events:
        if not 0x80 <= event.status <= 0xef:
            if channel_events_only:
                continue
            raise MidiError("SMF meta/SysEx cannot be imported as MIDI 2.0 channel events")
        events.append(TimedUmpEvent(event.tick, midi1_event_to_midi2(event, group)))
    return Midi2Sequence(events)
