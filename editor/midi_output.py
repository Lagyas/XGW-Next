"""MIDI playback through an explicitly selected external MIDI output.

Optional dependencies: mido + python-rtmidi. No port is opened automatically.
Timing uses monotonic clock and a worker thread; stop sends All Notes Off.
"""
import threading
import time
from midi import MidiError

def available_outputs():
    try:
        import mido
    except ImportError as exc:
        raise MidiError("MIDI output requires: pip install mido python-rtmidi") from exc
    try:
        return mido.get_output_names()
    except Exception as exc:
        raise MidiError(f"Cannot enumerate MIDI outputs: {exc}") from exc

def timed_messages(song):
    """Yield (seconds, MIDI bytes), with tempo map taken from all tracks.

    Supports PPQN SMF 0/1. Excludes SysEx/meta and other non-channel events.
    Stable ordering follows tick, track, event order.
    """
    if song.division & 0x8000 or song.division <= 0:
        raise MidiError("Playback of SMPTE-timed MIDI is not supported")
    events = []
    for track_idx, track in enumerate(song.tracks):
        for ev in track.events:
            events.append((ev.tick, track_idx, ev.order, ev))
    events.sort(key=lambda row: row[:3])
    tempo = 500000
    last_tick = 0
    seconds = 0.0
    for tick, _, _, ev in events:
        if tick < last_tick:
            raise MidiError("Negative MIDI event position")
        seconds += (tick - last_tick) * tempo / (song.division * 1000000)
        last_tick = tick
        if ev.status == 0xff and ev.meta_type == 0x51 and len(ev.data) == 3:
            new_tempo = int.from_bytes(ev.data, "big")
            if new_tempo > 0:
                tempo = new_tempo
        elif 0x80 <= ev.status <= 0xef:
            yield seconds, bytes((ev.status,)) + ev.data

class MidiPlayer:
    def __init__(self, on_state=None, on_error=None):
        self._thread = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self.on_state = on_state
        self.on_error = on_error

    @property
    def playing(self):
        return self._thread is not None and self._thread.is_alive()

    def play(self, song, port_name):
        if self.playing:
            raise MidiError("Playback is already active")
        if not port_name:
            raise MidiError("Choose a MIDI output")
        # Copy the event timeline before starting the worker thread.
        timeline = list(timed_messages(song))
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, args=(timeline, port_name), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self, timeline, port_name):
        port = None
        try:
            import mido
            port = mido.open_output(port_name)
            if self.on_state:
                self.on_state(True)
            started = time.monotonic()
            for offset, payload in timeline:
                if self._stop.wait(max(0.0, started + offset - time.monotonic())):
                    break
                if self._stop.is_set():
                    break
                port.send(mido.Message.from_bytes(list(payload)))
        except Exception as exc:
            if self.on_error:
                self.on_error(str(exc))
        finally:
            if port is not None:
                try:
                    # Send CC 123 (All Notes Off) on every channel, also on stop.
                    for channel in range(16):
                        port.send(mido.Message("control_change", channel=channel, control=123, value=0))
                    port.close()
                except Exception:
                    pass
            if self.on_state:
                self.on_state(False)
