"""MIDI playback through an explicitly selected external MIDI output.

Optional dependencies: mido + python-rtmidi. No port is opened automatically.
Timing uses monotonic clock and a worker thread; stop sends All Notes Off.
"""
import threading
import time
from midi import MidiError
from xg_sysex import smf_sysex_to_wire
from meter_grid import meter_changes
from fractions import Fraction

def validate_enabled_channels(channels):
    """Normalize a playback mask and reject invalid channel identifiers."""
    try:
        enabled = set(channels)
    except (TypeError, ValueError) as exc:
        raise MidiError("Invalid enabled MIDI channels") from exc
    if any(type(ch) is not int or not 0 <= ch <= 15 for ch in enabled):
        raise MidiError("Invalid enabled MIDI channels")
    return enabled


def validate_enabled_tracks(song, tracks):
    """Validate track selection before playback, without modifying the caller's set."""
    if tracks is None:
        return None
    try:
        selected = set(tracks)
    except (TypeError, ValueError) as exc:
        raise MidiError("Invalid enabled MIDI tracks") from exc
    if any(type(index) is not int or not 0 <= index < len(song.tracks) for index in selected):
        raise MidiError("Invalid enabled MIDI tracks")
    return selected


def available_outputs():
    try:
        import mido
    except ImportError as exc:
        raise MidiError("MIDI output requires: pip install mido python-rtmidi") from exc
    try:
        mido.set_backend("mido.backends.rtmidi")
        return mido.get_output_names()
    except Exception as exc:
        raise MidiError(f"Cannot enumerate MIDI outputs (RtMidi): {exc}") from exc

def chase_messages(song, start_tick, enabled_tracks=None, enabled_channels=None):
    """Restore channel state when playback starts inside a song.

    Chase bank select before program changes, then other controllers and
    pitch/pressure. Notes and SysEx are intentionally not chased: recreating
    their complete prior state safely needs dedicated policies.
    """
    if type(start_tick) is not int or not 0 <= start_tick <= 0x0fffffff:
        raise MidiError("Invalid playback start tick")
    enabled_tracks = validate_enabled_tracks(song, enabled_tracks)
    if enabled_channels is not None:
        enabled_channels = validate_enabled_channels(enabled_channels)
    if start_tick == 0:
        return []
    state = {}
    events = sorted(
        ((ev.tick, ti, ev.order, ev) for ti, track in enumerate(song.tracks)
         if enabled_tracks is None or ti in enabled_tracks
         for ev in track.events if ev.tick < start_tick),
        key=lambda item: item[:3])
    for _, _, _, ev in events:
        status = ev.status
        if not 0x80 <= status <= 0xef or (enabled_channels is not None and (status & 15) not in enabled_channels):
            continue
        kind = status & 0xf0
        if kind == 0xb0 and len(ev.data) == 2:
            controller, value = ev.data
            # Don't chase momentary controls such as sustain-off/reset/all-notes-off.
            if controller in (0, 32) or 1 <= controller <= 119 and controller not in (64, 66, 67):
                state[(status, controller)] = bytes((status, controller, value))
        elif kind in (0xc0, 0xd0) and len(ev.data) == 1:
            state[(status, -1)] = bytes((status, ev.data[0]))
        elif kind == 0xe0 and len(ev.data) == 2:
            state[(status, -1)] = bytes((status,)) + ev.data
    def priority(item):
        (status, cc), _ = item
        kind = status & 0xf0
        if kind == 0xb0 and cc == 0:
            return (0, status & 15, 0)
        if kind == 0xb0 and cc == 32:
            return (0, status & 15, 1)
        if kind == 0xc0:
            return (1, status & 15, 0)
        return (2, status & 15, cc)
    return [payload for _, payload in sorted(state.items(), key=priority)]


def timed_messages(song, include_sysex=False, enabled_tracks=None, start_tick=0, chase=True, enabled_channels=None):
    """Yield (seconds, MIDI bytes), with tempo map taken from all tracks.

    Supports PPQN SMF 0/1. Optionally emits complete F0 SysEx messages.\n    Incomplete or F7 continuation SysEx is skipped (not reconstructed).
    Stable ordering follows tick, track, event order.
    """
    if type(start_tick) is not int or not 0 <= start_tick <= 0x0fffffff:
        raise MidiError("Invalid playback start tick")
    enabled_tracks = validate_enabled_tracks(song, enabled_tracks)
    if enabled_channels is not None:
        enabled_channels = validate_enabled_channels(enabled_channels)
    if song.division & 0x8000 or song.division <= 0:
        raise MidiError("Playback of SMPTE-timed MIDI is not supported")
    if chase and start_tick:
        for payload in chase_messages(song, start_tick, enabled_tracks, enabled_channels):
            yield 0.0, payload
    events = []
    for track_idx, track in enumerate(song.tracks):
        for ev in track.events:
            if enabled_tracks is None or track_idx in enabled_tracks or (ev.status == 0xff and ev.meta_type == 0x51):
                events.append((ev.tick, track_idx, ev.order, ev))
    events.sort(key=lambda row: row[:3])
    tempo = 500000
    last_tick = 0
    seconds = 0.0
    start_seconds = None
    for tick, _, _, ev in events:
        if tick < last_tick:
            raise MidiError("Negative MIDI event position")
        seconds += (tick - last_tick) * tempo / (song.division * 1000000)
        last_tick = tick
        if start_seconds is None and tick >= start_tick:
            # Compute elapsed time at the requested tick, using the tempo
            # that was active before this event (including earlier changes).
            start_seconds = seconds - (tick - start_tick) * tempo / (song.division * 1000000)
        if ev.status == 0xff and ev.meta_type == 0x51 and len(ev.data) == 3:
            new_tempo = int.from_bytes(ev.data, "big")
            if new_tempo > 0:
                tempo = new_tempo
        elif include_sysex and ev.status == 0xf0:
            raw = smf_sysex_to_wire(ev.status, ev.data)
            if raw is not None:
                if tick >= start_tick:
                    yield seconds - start_seconds, raw
        elif 0x80 <= ev.status <= 0xef:
            if tick >= start_tick and (enabled_channels is None or (ev.status & 15) in enabled_channels):
                yield seconds - start_seconds, bytes((ev.status,)) + ev.data

def tick_seconds(song, tick):
    """Elapsed seconds at a tick, accounting for all valid tempo changes."""
    if type(tick) is not int or not 0 <= tick <= 0x0fffffff:
        raise MidiError("Invalid MIDI tick")
    if song.division & 0x8000 or song.division <= 0:
        raise MidiError("Playback of SMPTE-timed MIDI is not supported")
    tempos = sorted(
        (ev.tick, ti, ev.order, int.from_bytes(ev.data, "big"))
        for ti, track in enumerate(song.tracks) for ev in track.events
        if ev.status == 0xff and ev.meta_type == 0x51 and len(ev.data) == 3
        and ev.tick <= tick)
    current = 500000
    previous = 0
    elapsed = 0.0
    for event_tick, _, _, value in tempos:
        if event_tick < previous:
            continue
        elapsed += (event_tick - previous) * current / (song.division * 1000000)
        previous = event_tick
        if value > 0:
            current = value
    return elapsed + (tick - previous) * current / (song.division * 1000000)


def loop_messages(song, start_tick, end_tick, include_sysex=False, enabled_tracks=None, enabled_channels=None):
    """One loop pass as (offset_seconds, payload), plus its exact duration.

    Returns a finite timeline to be repeatedly scheduled by MidiPlayer. Notes
    sounding over the loop boundary are silenced by the player, not carried to
    the next iteration. State chase is recalculated at the loop start.
    """
    if (type(start_tick) is not int or type(end_tick) is not int
            or not 0 <= start_tick < end_tick <= 0x0fffffff):
        raise MidiError("Loop end must be greater than loop start")
    duration = tick_seconds(song, end_tick) - tick_seconds(song, start_tick)
    if duration <= 0:
        raise MidiError("Loop duration must be positive")
    timeline = [(time_offset, payload) for time_offset, payload in
                timed_messages(song, include_sysex=include_sysex,
                               enabled_tracks=enabled_tracks, start_tick=start_tick, enabled_channels=enabled_channels)
                if time_offset < duration]
    return timeline, duration


def metronome_messages(song, start_tick, end_tick, channel=9, strong_note=76,
                       weak_note=77, velocity=90, click_ticks=24):
    """Generate timed MIDI click note pairs in [start_tick, end_tick).

    Meter changes restart the beat phase. Output times are relative to start_tick
    and follow the song's tempo map. The chosen output channel is configurable.
    """
    if (type(start_tick) is not int or type(end_tick) is not int
            or not 0 <= start_tick < end_tick <= 0x0fffffff
            or any(type(v) is not int for v in (channel, strong_note, weak_note, velocity, click_ticks))
            or not 0 <= channel <= 15 or not 0 <= strong_note <= 127
            or not 0 <= weak_note <= 127 or not 1 <= velocity <= 127
            or not 1 <= click_ticks <= song.division):
        raise MidiError("Invalid metronome settings")
    changes = meter_changes(song)
    base = tick_seconds(song, start_tick)
    result = []
    for i, (origin, numerator, denominator) in enumerate(changes):
        stop = min(end_tick, changes[i + 1][0] if i + 1 < len(changes) else end_tick)
        if origin >= stop:
            continue
        beat = Fraction(song.division * 4, denominator)
        index = 0
        while True:
            position = Fraction(origin) + index * beat
            if position >= stop:
                break
            tick = round(position)
            if start_tick <= tick < stop:
                note = strong_note if index % numerator == 0 else weak_note
                duration = min(click_ticks, max(1, round(beat / 4)))
                off_tick = min(tick + duration, end_tick)
                result.append((tick_seconds(song, tick) - base,
                               bytes((0x90 | channel, note, velocity))))
                result.append((tick_seconds(song, off_tick) - base,
                               bytes((0x80 | channel, note, 0))))
            index += 1
    return sorted(result, key=lambda pair: pair[0])


def count_in_messages(song, start_tick, bars=1, channel=9, strong_note=76,
                      weak_note=77, velocity=90):
    """Return (negative seconds, MIDI bytes) for a metronome count-in.

    Beat length and tempo are taken from the meter/tempo active at start_tick.
    The final count-in beat ends before the song begins (time zero).
    """
    if type(bars) is not int or not 0 <= bars <= 8:
        raise MidiError('Count-in must be 0–8 bars')
    if type(start_tick) is not int or not 0 <= start_tick <= 0x0fffffff:
        raise MidiError('Invalid count-in start tick')
    if not 0 <= channel <= 15:
        raise MidiError('Invalid count-in channel')
    if bars == 0:
        return [], 0.0
    meter = (4, 4)
    for tick, numerator, denominator in meter_changes(song):
        if tick <= start_tick:
            meter = (numerator, denominator)
    numerator, denominator = meter
    beat_ticks = song.division * 4 / denominator
    # Evaluate local seconds-per-tick at the count-in boundary.
    from bisect import bisect_right
    changes = sorted((ev.tick, ti, ev.order, int.from_bytes(ev.data, 'big'))
                     for ti, track in enumerate(song.tracks) for ev in track.events
                     if ev.status == 0xff and ev.meta_type == 0x51
                     and len(ev.data) == 3 and int.from_bytes(ev.data, 'big') > 0)
    tempo = 500000
    for tick, _, _, value in changes:
        if tick <= start_tick:
            tempo = value
    beat_seconds = beat_ticks * tempo / (song.division * 1000000)
    count = numerator * bars
    duration = count * beat_seconds
    messages = []
    for i in range(count):
        offset = (i - count) * beat_seconds
        note = strong_note if i % numerator == 0 else weak_note
        messages.append((offset, bytes((0x90 | channel, note, velocity))))
        messages.append((min(offset + beat_seconds / 4, -1e-6),
                         bytes((0x80 | channel, note, 0))))
    return messages, duration


def silence_channels(port, mido):
    """Release pedals, silence notes and reset pitch safely at stop/boundary."""
    for channel in range(16):
        port.send(mido.Message("control_change", channel=channel, control=64, value=0))
        port.send(mido.Message("control_change", channel=channel, control=66, value=0))
        port.send(mido.Message("control_change", channel=channel, control=123, value=0))


class MidiPlayer:
    def __init__(self, on_state=None, on_error=None):
        self._thread = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._enabled_channels = set(range(16))
        self._pending_silence = set()
        self._live_cc = {}
        self._activity = [0] * 16
        self._routed_active = False
        self._routed_ports = set()
        self._routed_cc = {}
        self._routed_sysex = []
        self._routed_activity = {}
        self._routed_silence = set()
        self._routed_enabled = set()
        self.on_state = on_state
        self.on_error = on_error

    @property
    def playing(self):
        return self._thread is not None and self._thread.is_alive()

    def set_enabled_channels(self, channels):
        """Change playback-only channel audibility safely from the UI thread."""
        enabled = validate_enabled_channels(channels)
        with self._lock:
            self._pending_silence.update(self._enabled_channels - enabled)
            self._enabled_channels = enabled
        self._wake.set()

    def send_live_cc(self, channel, controller, value):
        """Queue a live controller change for the playback output thread."""
        if any(type(v) is not int for v in (channel, controller, value)) or not (0 <= channel < 16 and 0 <= controller < 120 and 0 <= value < 128):
            raise MidiError("Invalid live MIDI controller")
        if not self.playing:
            return False
        with self._lock:
            self._live_cc[(channel, controller)] = value
        self._wake.set()
        return True

    def send_routed_cc(self, port_name, channel, controller, value):
        """Queue a controller for one physical port/channel pair."""
        if (not isinstance(port_name, str) or not port_name.strip() or
                any(type(v) is not int for v in (channel, controller, value)) or
                not 0 <= channel < 16 or not 0 <= controller < 120 or not 0 <= value < 128):
            raise MidiError("Invalid routed MIDI controller")
        if not self.playing or not getattr(self, '_routed_active', False):
            return False
        with self._lock:
            if port_name not in self._routed_ports:
                raise MidiError("MIDI output is not active")
            self._routed_cc[(port_name, channel, controller)] = value
        self._wake.set()
        return True

    def send_routed_sysex(self, port_name, wire):
        """Queue a complete SysEx for the named, active physical MIDI output.

        Validation happens before queue mutation; the worker owns the port.
        """
        if not isinstance(port_name, str) or not port_name.strip():
            raise MidiError("Invalid routed MIDI output")
        if (not isinstance(wire, (bytes, bytearray)) or len(wire) < 3 or
                wire[0] != 0xf0 or wire[-1] != 0xf7 or
                any(value > 127 for value in wire[1:-1])):
            raise MidiError("Expected a complete 7-bit MIDI SysEx message")
        if not self.playing or not self._routed_active:
            return False
        with self._lock:
            if port_name not in self._routed_ports:
                raise MidiError("MIDI output is not active")
            self._routed_sysex.append((port_name, bytes(wire)))
        self._wake.set()
        return True

    def routed_activity_snapshot(self):
        with self._lock:
            return dict(getattr(self, '_routed_activity', {}))

    def set_routed_enabled(self, enabled):
        """Set audibility for (port, channel) pairs, silencing removed pairs."""
        if not isinstance(enabled, (set, frozenset)) or any(
                not isinstance(pair, tuple) or len(pair) != 2 or
                not isinstance(pair[0], str) or type(pair[1]) is not int or
                not 0 <= pair[1] < 16 for pair in enabled):
            raise MidiError("Invalid routed channel mask")
        with self._lock:
            old = getattr(self, '_routed_enabled', set())
            self._routed_silence.update(old - enabled)
            self._routed_enabled = set(enabled)
        self._wake.set()

    def activity_snapshot(self):
        """Monotonic per-channel MIDI message counters (safe for GUI polling)."""
        with self._lock:
            return tuple(self._activity)

    def _drain_live_cc(self, port, mido):
        with self._lock:
            pending = self._live_cc
            self._live_cc = {}
            enabled = self._enabled_channels.copy()
        for (channel, controller), value in pending.items():
            if channel in enabled:
                port.send(mido.Message("control_change", channel=channel, control=controller, value=value))

    def _current_channel_state(self):
        with self._lock:
            silenced = self._pending_silence.copy()
            self._pending_silence.clear()
            return self._enabled_channels.copy(), silenced

    def play(self, song, port_name, include_sysex=False, enabled_tracks=None, start_tick=0,
             loop_start=None, loop_end=None, metronome=False, click_channel=9, start_at=None, count_in_bars=0, enabled_channels=None, restore_held_notes=False):
        if self.playing:
            raise MidiError("Playback is already active")
        initial_channels = (set(range(16)) if enabled_channels is None
                            else validate_enabled_channels(enabled_channels))
        enabled_tracks = validate_enabled_tracks(song, enabled_tracks)
        if not port_name:
            raise MidiError("Choose a MIDI output")
        # Copy the event timeline before starting the worker thread.
        loop_duration = None
        repeat_timeline = None
        first_duration = None
        if loop_start is not None or loop_end is not None:
            if loop_start is None or loop_end is None:
                raise MidiError("Both loop start and loop end are required")
            repeat_timeline, loop_duration = loop_messages(
                song, loop_start, loop_end, include_sysex=include_sysex,
                enabled_tracks=enabled_tracks, enabled_channels=None)
            # The first pass starts at the transport cursor, even before L.
            # Only subsequent passes repeat the full L-R region.
            first_duration = tick_seconds(song, loop_end) - tick_seconds(song, start_tick)
            timeline = [(offset, payload) for offset, payload in timed_messages(
                song, include_sysex=include_sysex, enabled_tracks=enabled_tracks,
                start_tick=start_tick, enabled_channels=None) if offset < first_duration]
        else:
            timeline = list(timed_messages(song, include_sysex=include_sysex,
                                           enabled_tracks=enabled_tracks, start_tick=start_tick, enabled_channels=None))
        if repeat_timeline is not None:
            from loop_boundary import single_port_loop_prefix
            # Do not duplicate controller chase: loop_messages already starts
            # with its own chase. Replace that prefix with full channel/note
            # restoration, preserving events exactly at the left locator.
            chase_at_left = chase_messages(song, loop_start, enabled_tracks, None)
            repeat_timeline = (single_port_loop_prefix(
                song, port_name, loop_start, enabled_tracks)
                + repeat_timeline[len(chase_at_left):])
        if restore_held_notes and start_tick:
            from note_chase import held_notes
            restored = [(0.0, payload) for _, payload in held_notes(
                song, start_tick, default_port=port_name, enabled_tracks=enabled_tracks,
                enabled_channels=initial_channels)]
            # Controller/program chase must precede the restored note-ons.
            chase_count = len(chase_messages(song, start_tick, enabled_tracks, initial_channels))
            timeline[chase_count:chase_count] = restored
        if metronome:
            if loop_duration is not None:
                # First pass follows the cursor; repeats follow the L/R locators.
                first_clicks = metronome_messages(song, start_tick, loop_end, channel=click_channel)
                repeat_clicks = metronome_messages(song, loop_start, loop_end, channel=click_channel)
                timeline = sorted(timeline + first_clicks, key=lambda item: item[0])
                repeat_timeline = sorted(repeat_timeline + repeat_clicks, key=lambda item: item[0])
            else:
                first = start_tick
                last = max((ev.tick for track in song.tracks for ev in track.events), default=first)
                last = max(first + song.division * 4, last)
                clicks = metronome_messages(song, first, last, channel=click_channel)
                timeline = sorted(timeline + clicks, key=lambda item: item[0])
        if count_in_bars:
            count_clicks, _ = count_in_messages(song, start_tick, count_in_bars,
                                                 channel=click_channel)
            timeline = sorted(timeline + count_clicks, key=lambda item: item[0])
        if start_at is not None and (type(start_at) not in (int, float) or not 0 <= start_at < float("inf")):
            raise MidiError("Invalid shared transport start time")
        self._stop.clear()
        self._wake.clear()
        with self._lock:
            self._enabled_channels = initial_channels
            self._pending_silence.clear()
            self._live_cc.clear()
            self._activity = [0] * 16
        self._thread = threading.Thread(target=self._run,
                                        args=(timeline, port_name, loop_duration, repeat_timeline, first_duration, start_at), daemon=True)
        self._thread.start()

    def play_routed(self, song, routes, default_port, start_tick=0, loop_start=None,
                    loop_end=None, include_sysex=False, enabled_tracks=None,
                    metronome=False, click_channel=9, click_port=None, start_at=None, count_in_bars=0,
                    restore_held_notes=False):
        """Play routed tracks on independent physical MIDI outputs."""
        from midi_routing import routed_messages, validate_routes
        if self.playing:
            raise MidiError('Playback is already active')
        validate_routes(song, routes, default_port)
        if (loop_start is None) != (loop_end is None):
            raise MidiError('Both loop locators are required')
        if loop_start is not None and not (0 <= loop_start < loop_end and start_tick < loop_end):
            raise MidiError('Invalid loop locators')
        first = list(routed_messages(song, routes, default_port, start_tick, loop_end,
                                     enabled_tracks, include_sysex))
        repeated = (list(routed_messages(song, routes, default_port, loop_start, loop_end,
                                         enabled_tracks, include_sysex)) if loop_start is not None else None)
        if repeated is not None:
            from loop_boundary import routed_loop_prefix
            repeated = routed_loop_prefix(song, routes, default_port, loop_start,
                                          enabled_tracks) + repeated
        first_duration = (tick_seconds(song, loop_end) - tick_seconds(song, start_tick)
                          if loop_start is not None else None)
        duration = (tick_seconds(song, loop_end) - tick_seconds(song, loop_start)
                    if loop_start is not None else None)
        from multiport_chase import chase_messages
        chase = chase_messages(song, routes, default_port, start_tick, enabled_tracks)
        restored = []
        if restore_held_notes and start_tick:
            from note_chase import held_notes
            restored = [(0.0, port, payload) for port, payload in held_notes(
                song, start_tick, routes, default_port, enabled_tracks)]
        first = [(0.0, port, payload) for port, payload in chase] + restored + first
        if metronome:
            target = click_port or default_port
            if not target:
                raise MidiError('Choose a metronome MIDI output')
            end = loop_end if loop_end is not None else max(
                start_tick + song.division * 4,
                max((ev.tick for tr in song.tracks for ev in tr.events), default=start_tick))
            first += [(offset, target, payload) for offset, payload in
                      metronome_messages(song, start_tick, end, channel=click_channel)]
            first.sort(key=lambda row: row[0])
            if repeated is not None:
                repeated += [(offset, target, payload) for offset, payload in
                             metronome_messages(song, loop_start, loop_end, channel=click_channel)]
                repeated.sort(key=lambda row: row[0])
        if count_in_bars:
            clicks, _ = count_in_messages(song, start_tick, count_in_bars, channel=click_channel)
            target = click_port or default_port
            if not target:
                raise MidiError('Choose a count-in MIDI output')
            first.extend((offset, target, payload) for offset, payload in clicks)
            first.sort(key=lambda row: row[0])
        ports = {port for _, port, _ in first}
        if repeated is not None:
            ports.update(port for _, port, _ in repeated)
        ports.update(port for port, _ in validate_routes(song, routes, default_port).values())
        if default_port:
            ports.add(default_port)
        self._stop.clear()
        self._wake.clear()
        with self._lock:
            self._activity = [0] * 16
            self._live_cc.clear()
            self._enabled_channels = set(range(16))
        with self._lock:
            self._routed_ports = set(ports)
            self._routed_active = True
            self._routed_cc = {}
            self._routed_sysex = []
            self._routed_activity = {}
            self._routed_silence = set()
            self._routed_enabled = {(port, channel) for port in ports for channel in range(16)}
        self._thread = threading.Thread(target=self._run_routed,
                        args=(first, repeated, first_duration, duration, ports, start_at), daemon=True)
        self._thread.start()

    def _drain_routed(self, opened, mido):
        with self._lock:
            queued = self._routed_cc
            self._routed_cc = {}
            sysex = self._routed_sysex
            self._routed_sysex = []
            silenced = self._routed_silence
            self._routed_silence = set()
            enabled = self._routed_enabled.copy()
        for name, channel in silenced:
            if name in opened:
                for controller in (64, 66, 123):
                    opened[name].send(mido.Message('control_change', channel=channel,
                                                    control=controller, value=0))
        for (name, channel, controller), value in queued.items():
            if name in opened and (name, channel) in enabled:
                opened[name].send(mido.Message('control_change', channel=channel,
                                                control=controller, value=value))
        for name, wire in sysex:
            if name in opened:
                opened[name].send(mido.Message('sysex', data=list(wire[1:-1])))
        return enabled

    def _run_routed(self, first, repeated, first_duration, duration, port_names, start_at=None):
        opened = {}
        try:
            import mido
            mido.set_backend('mido.backends.rtmidi')
            for name in sorted(port_names):
                opened[name] = mido.open_output(name)
            if self.on_state:
                self.on_state(True)
            start = time.monotonic() if start_at is None else start_at
            timeline = first
            first_pass = True
            while not self._stop.is_set():
                for offset, name, payload in timeline:
                    deadline = start + offset
                    while not self._stop.is_set():
                        self._drain_routed(opened, mido)
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            break
                        self._wake.wait(remaining)
                        self._wake.clear()
                    if self._stop.is_set():
                        break
                    enabled = self._drain_routed(opened, mido)
                    if payload[0] == 0xf0:
                        opened[name].send(mido.Message('sysex', data=list(payload[1:-1])))
                    elif (name, payload[0] & 15) in enabled:
                        opened[name].send(mido.Message.from_bytes(list(payload)))
                        with self._lock:
                            key = (name, payload[0] & 15)
                            self._routed_activity[key] = self._routed_activity.get(key, 0) + 1
                            self._activity[payload[0] & 15] += 1
                if repeated is None or self._stop.is_set():
                    break
                start += first_duration if first_pass else duration
                first_pass = False
                timeline = repeated
                if self._stop.wait(max(0, start - time.monotonic())):
                    break
                for port in opened.values():
                    silence_channels(port, mido)
        except Exception as exc:
            if self.on_error:
                self.on_error(str(exc))
        finally:
            with self._lock:
                self._routed_active = False
                self._routed_cc = {}
                self._routed_sysex = []
            for port in opened.values():
                try:
                    silence_channels(port, mido)
                    port.close()
                except Exception:
                    pass
            if self.on_state:
                self.on_state(False)

    def stop(self):
        self._stop.set()
        self._wake.set()

    def wait_stopped(self, timeout=1.0):
        """Wait for the MIDI worker to release its output port."""
        thread = self._thread
        if thread is None:
            return True
        if thread is threading.current_thread():
            return False
        thread.join(timeout)
        return not thread.is_alive()

    def _run(self, timeline, port_name, loop_duration=None, repeat_timeline=None, first_duration=None, start_at=None):
        port = None
        try:
            import mido
            mido.set_backend("mido.backends.rtmidi")
            port = mido.open_output(port_name)
            if self.on_state:
                self.on_state(True)
            started = time.monotonic() if start_at is None else start_at
            first_pass = True
            while not self._stop.is_set():
                for offset, payload in timeline:
                    deadline = started + offset
                    while not self._stop.is_set():
                        self._drain_live_cc(port, mido)
                        enabled, silenced = self._current_channel_state()
                        for ch in silenced:
                            port.send(mido.Message("control_change", channel=ch, control=64, value=0))
                            port.send(mido.Message("control_change", channel=ch, control=66, value=0))
                            port.send(mido.Message("control_change", channel=ch, control=123, value=0))
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            break
                        self._wake.wait(remaining)
                        self._wake.clear()
                    if self._stop.is_set():
                        break
                    enabled, silenced = self._current_channel_state()
                    for ch in silenced:
                        port.send(mido.Message("control_change", channel=ch, control=64, value=0))
                        port.send(mido.Message("control_change", channel=ch, control=66, value=0))
                        port.send(mido.Message("control_change", channel=ch, control=123, value=0))
                    self._drain_live_cc(port, mido)
                    if payload[0] == 0xf0:
                        port.send(mido.Message('sysex', data=list(payload[1:-1])))
                    elif (payload[0] & 15) in enabled:
                        port.send(mido.Message.from_bytes(list(payload)))
                        with self._lock:
                            self._activity[payload[0] & 15] += 1
                if self._stop.is_set() or loop_duration is None:
                    break
                started += first_duration if first_pass and first_duration is not None else loop_duration
                first_pass = False
                if repeat_timeline is not None:
                    timeline = repeat_timeline
                if self._stop.wait(max(0.0, started - time.monotonic())):
                    break
                silence_channels(port, mido)
        except Exception as exc:
            if self.on_error:
                self.on_error(str(exc))
        finally:
            with self._lock:
                self._live_cc.clear()
            if port is not None:
                try:
                    silence_channels(port, mido)
                    port.close()
                except Exception:
                    pass
            if self.on_state:
                self.on_state(False)
