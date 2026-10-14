"""MIDI 1.0 live input capture, independent of Tk and the playback worker.

Capture is quantized only to the song's tick clock; no musical snap is applied.
Optionally follows the song tempo map during recording.
"""
import threading
from contextlib import ExitStack
import time
from midi import Event, MidiError, Track
from midi_output import tick_seconds


def available_inputs():
    try:
        import mido
        mido.set_backend('mido.backends.rtmidi')
        return mido.get_input_names()
    except ImportError as exc:
        raise MidiError('MIDI input requires: pip install mido python-rtmidi') from exc
    except Exception as exc:
        raise MidiError(f'Cannot enumerate MIDI inputs (RtMidi): {exc}') from exc


class SongTempoClock:
    """Convert elapsed monotonic seconds into ticks across tempo changes."""

    def __init__(self, song, start_tick=0):
        if type(start_tick) is not int or not 0 <= start_tick <= 0x0fffffff:
            raise MidiError('Invalid recording start tick')
        if song.division <= 0 or song.division & 0x8000:
            raise MidiError('Recording requires PPQN timing')
        self.division = song.division
        changes = sorted(
            (e.tick, ti, e.order, int.from_bytes(e.data, 'big'))
            for ti, track in enumerate(song.tracks) for e in track.events
            if e.status == 0xff and e.meta_type == 0x51
            and len(e.data) == 3 and int.from_bytes(e.data, 'big') > 0)
        tempo = 500000
        for tick, _, _, value in changes:
            if tick <= start_tick:
                tempo = value
        self.segments = [(0.0, start_tick, tempo)]
        origin = tick_seconds(song, start_tick)
        for tick, _, _, value in changes:
            if tick > start_tick:
                self.segments.append((tick_seconds(song, tick) - origin, tick, value))
        self.times = [segment[0] for segment in self.segments]

    def tick_at(self, elapsed_seconds):
        if (type(elapsed_seconds) not in (float, int)
                or not 0 <= elapsed_seconds < float('inf')):
            raise MidiError('Invalid recording timestamp')
        from bisect import bisect_right
        i = bisect_right(self.times, elapsed_seconds) - 1
        origin, tick, tempo = self.segments[i]
        result = tick + round((elapsed_seconds - origin) * self.division * 1000000 / tempo)
        if result > 0x0fffffff:
            raise MidiError('Recording exceeds maximum MIDI tick')
        return result


class CaptureBuffer:
    """Thread-safe collection of MIDI channel events with stable tick ordering."""
    def __init__(self, division, bpm=120.0, start_tick=0, punch_start=None, punch_end=None, song=None, latency_ms=0, input_channel=None, output_channel=None):
        if input_channel is not None and (type(input_channel) is not int or not 0 <= input_channel <= 15):
            raise MidiError("Input channel must be 1–16 or All")
        if output_channel is not None and (type(output_channel) is not int or not 0 <= output_channel <= 15):
            raise MidiError("Output channel must be 1–16 or Keep")
        self.input_channel = input_channel
        self.output_channel = output_channel
        if (type(latency_ms) not in (int, float) or not -500 <= latency_ms <= 500):
            raise MidiError("Recording latency must be between -500 and 500 ms")
        if (type(division) is not int or not 1 <= division <= 0x7fff
                or type(start_tick) is not int or not 0 <= start_tick <= 0x0fffffff
                or type(bpm) not in (float, int) or not 1 <= bpm <= 1000):
            raise MidiError('Invalid recording clock')
        if (punch_start is None) != (punch_end is None):
            raise MidiError('Punch requires both start and end ticks')
        if punch_start is not None and (type(punch_start) is not int or type(punch_end) is not int
                or not 0 <= punch_start < punch_end <= 0x0fffffff):
            raise MidiError('Invalid punch range')
        self.punch_start, self.punch_end = punch_start, punch_end
        self.latency_ms = latency_ms
        if song is not None and song.division != division:
            raise MidiError("Recording division differs from song")
        self._tempo_clock = SongTempoClock(song, start_tick) if song is not None else None
        self._active_notes = {}
        self.division = division
        self.bpm = bpm
        self.start_tick = start_tick
        self._events = []
        self._last_tick = start_tick
        self._lock = threading.Lock()

    def feed(self, raw, elapsed_seconds):
        if not isinstance(raw, (bytes, bytearray)) or not raw:
            raise MidiError('Invalid MIDI input bytes')
        status = raw[0]
        kind = status & 0xf0
        expected = 1 if kind in (0xc0, 0xd0) else 2
        if not (0x80 <= status <= 0xef and len(raw) == expected + 1
                and all(value <= 127 for value in raw[1:])):
            return False  # Ignore SysEx, clocks and unsupported messages.
        if self.input_channel is not None and (status & 0x0f) != self.input_channel:
            return False
        if self.output_channel is not None:
            status = (status & 0xf0) | self.output_channel
        if not isinstance(elapsed_seconds, (int, float)) or not 0 <= elapsed_seconds < float('inf'):
            raise MidiError('Invalid recording timestamp')
        adjusted_seconds = max(0.0, elapsed_seconds - self.latency_ms / 1000.0)
        tick = (self._tempo_clock.tick_at(adjusted_seconds) if self._tempo_clock is not None
                else self.start_tick + round(adjusted_seconds * self.division * self.bpm / 60))
        if tick > 0x0fffffff:
            raise MidiError('Recording exceeds maximum MIDI tick')
        if self.punch_start is not None:
            if tick < self.punch_start:
                return False
            if tick >= self.punch_end:
                return False
        with self._lock:
            self._last_tick = max(self._last_tick, tick)
            note_key = (status & 0x0f, raw[1]) if kind in (0x80, 0x90) else None
            note_on = kind == 0x90 and raw[2] > 0
            note_off = kind == 0x80 or (kind == 0x90 and raw[2] == 0)
            if note_off and note_key not in self._active_notes:
                return False if self.punch_start is not None else self._append(tick, status, raw[1:])
            if note_on:
                self._active_notes[note_key] = self._active_notes.get(note_key, 0) + 1
            elif note_off:
                self._active_notes[note_key] -= 1
                if not self._active_notes[note_key]:
                    del self._active_notes[note_key]
            return self._append(tick, status, raw[1:])

    def _append(self, tick, status, data):
        self._events.append(Event(tick, status, bytes(data), order=len(self._events)))
        return True

    def events(self, stop_tick=None):
        """Return a playable take, closing all still-held notes at stop/punch-out."""
        if stop_tick is not None and (type(stop_tick) is not int or not 0 <= stop_tick <= 0x0fffffff):
            raise MidiError("Invalid recording stop tick")
        with self._lock:
            # Close notes still sounding at punch-out so the take cannot leave stuck notes.
            result = [Event(e.tick, e.status, e.data, e.meta_type, e.order)
                      for e in self._events]
            boundary = self.punch_end if self.punch_end is not None else stop_tick
            if boundary is not None:
                boundary = max(self._last_tick, boundary) if self.punch_end is None else boundary
                for (channel, note), count in sorted(self._active_notes.items()):
                    for _ in range(count):
                        result.append(Event(boundary, 0x80 | channel,
                                            bytes((note, 0)), order=len(result)))
            return sorted((Event(e.tick, e.status, e.data, e.meta_type, e.order)
                           for e in result), key=lambda e: (e.tick, e.order))


class MidiRecorder:
    """Capture an RtMidi input on a worker; call finish() to obtain a Track."""
    def __init__(self, on_error=None):
        self.on_error = on_error
        self._stop = threading.Event()
        self._thread = None
        self._capture = None
        self._started_at = None

    @property
    def recording(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self, port_name, division, bpm=120.0, start_tick=0, punch_start=None, punch_end=None, song=None, start_at=None, latency_ms=0, input_channel=None, output_channel=None, monitor_port=None):
        if self.recording:
            raise MidiError('Recording is already active')
        if not port_name:
            raise MidiError('Choose a MIDI input')
        if monitor_port is not None and (not isinstance(monitor_port, str) or not monitor_port.strip()):
            raise MidiError('Choose a MIDI monitoring output')
        if start_at is not None and (type(start_at) not in (int, float) or not 0 <= start_at < float("inf")):
            raise MidiError("Invalid shared transport start time")
        capture = CaptureBuffer(division, bpm, start_tick, punch_start, punch_end,
                                song=song, latency_ms=latency_ms,
                                input_channel=input_channel, output_channel=output_channel)
        self._capture = capture
        self._started_at = time.monotonic() if start_at is None else start_at
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, args=(port_name, capture, monitor_port), daemon=True)
        self._thread.start()

    def _run(self, name, capture, monitor_port=None):
        # Monitoring is performed by the input worker, never from the Tk thread.
        # A separate output port is opened only when explicitly requested.
        active = {}
        try:
            import mido
            mido.set_backend('mido.backends.rtmidi')
            with ExitStack() as stack:
                port = stack.enter_context(mido.open_input(name))
                output = stack.enter_context(mido.open_output(monitor_port)) if monitor_port else None

                def process(message):
                    raw = bytes(message.bytes())
                    accepted = capture.feed(raw, max(0.0, time.monotonic() - self._started_at))
                    if not accepted or output is None:
                        return
                    # Use the same channel mapping as the recorded events.
                    status = raw[0]
                    if capture.output_channel is not None:
                        status = (status & 0xf0) | capture.output_channel
                    payload = bytes((status,)) + raw[1:]
                    kind = status & 0xf0
                    if kind in (0x80, 0x90):
                        key = (status & 15, raw[1])
                        if kind == 0x90 and raw[2] > 0:
                            active[key] = active.get(key, 0) + 1
                        elif key in active:
                            active[key] -= 1
                            if active[key] <= 0:
                                del active[key]
                    output.send(mido.Message.from_bytes(list(payload)))

                try:
                    while not self._stop.wait(0.005):
                        for message in port.iter_pending():
                            process(message)
                    for message in port.iter_pending():
                        process(message)
                finally:
                    if output is not None:
                        # Never leave monitored notes hanging on stop/error.
                        for (channel, note), count in active.items():
                            for _ in range(count):
                                output.send(mido.Message('note_off', channel=channel,
                                                         note=note, velocity=0))
        except Exception as exc:
            if self.on_error:
                self.on_error(str(exc))

    def current_tick(self, now=None):
        """Current recording cursor, using the same clock as captured events.

        Return None when no take is active; clamp pre-roll to its start tick.
        """
        if not self.recording or self._capture is None or self._started_at is None:
            return None
        if now is None:
            now = time.monotonic()
        elapsed = max(0.0, now - self._started_at)
        capture = self._capture
        if capture._tempo_clock is not None:
            return capture._tempo_clock.tick_at(elapsed)
        return min(0x0fffffff, capture.start_tick + round(
            elapsed * capture.division * capture.bpm / 60))

    def finish(self):
        stopped_at = time.monotonic()
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                raise MidiError('MIDI input did not stop in time')
        self._thread = None
        if self._capture is None:
            return Track([])
        elapsed = max(0, stopped_at - self._started_at)
        tick = (self._capture._tempo_clock.tick_at(elapsed)
                if self._capture._tempo_clock is not None else
                self._capture.start_tick + round(
                    elapsed * self._capture.division * self._capture.bpm / 60))
        return Track(self._capture.events(stop_tick=min(tick, 0x0fffffff)))
