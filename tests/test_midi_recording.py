import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import MidiError
from midi_recording import CaptureBuffer, available_inputs

class RecordingTests(unittest.TestCase):
    def test_note_capture_tick_and_order(self):
        capture = CaptureBuffer(480, bpm=120, start_tick=960)
        self.assertTrue(capture.feed(bytes((0x90, 60, 100)), 0))
        self.assertTrue(capture.feed(bytes((0x80, 60, 0)), .5))
        self.assertEqual([(e.tick, e.status, e.data) for e in capture.events()], [
            (960, 0x90, b'\x3c\x64'), (1440, 0x80, b'\x3c\x00')])

    def test_same_tick_order(self):
        capture = CaptureBuffer(480)
        capture.feed(b'\xb0\x00\x7f', 0)
        capture.feed(b'\xc0\x15', 0)
        self.assertEqual([e.status for e in capture.events()], [0xb0, 0xc0])

    def test_reject_invalid_clock(self):
        for arguments in [(0, 120, 0), (0x8000, 120, 0), (480, 0, 0), (480, 120, -1)]:
            with self.assertRaises(MidiError):
                CaptureBuffer(*arguments)

    def test_ignore_unsupported_messages(self):
        capture = CaptureBuffer(480)
        self.assertFalse(capture.feed(b'\xf8', 1))
        self.assertFalse(capture.feed(b'\xf0\x01\xf7', 1))
        self.assertFalse(capture.feed(b'\x90\x80\x01', 1))
        self.assertEqual(capture.events(), [])

    def test_timestamp_validation(self):
        capture = CaptureBuffer(480)
        with self.assertRaises(MidiError):
            capture.feed(b'\x90\x3c\x64', -1)
        with self.assertRaises(MidiError):
            capture.feed(b'\x90\x3c\x64', float('nan'))

    def test_enumerate_inputs(self):
        class FakeMido:
            def set_backend(self, name):
                self.backend = name
            def get_input_names(self):
                return ['Keyboard']
        fake = FakeMido()
        with patch.dict(sys.modules, {'mido': fake}):
            self.assertEqual(available_inputs(), ['Keyboard'])
        self.assertEqual(fake.backend, 'mido.backends.rtmidi')

class PunchRecordingTests(unittest.TestCase):
    def test_punch_filters_and_closes_note(self):
        capture = CaptureBuffer(480, 120, 0, 480, 960)
        self.assertFalse(capture.feed(b'\x90\x3c\x64', .1))
        self.assertFalse(capture.feed(b'\x80\x3c\x00', .2))
        self.assertTrue(capture.feed(b'\x90\x40\x64', .6))
        self.assertTrue(capture.feed(b'\xb0\x07\x60', .7))
        self.assertFalse(capture.feed(b'\x80\x40\x00', 1.1))
        self.assertEqual([(e.tick, e.status, e.data) for e in capture.events()],
                         [(576, 0x90, b'\x40\x64'), (672, 0xb0, b'\x07\x60'),
                          (960, 0x80, b'\x40\x00')])

    def test_punch_note_off_inside_window(self):
        capture = CaptureBuffer(480, 120, 0, 100, 800)
        capture.feed(b'\x90\x3c\x50', .2)
        capture.feed(b'\x80\x3c\x00', .4)
        self.assertEqual(len(capture.events()), 2)

    def test_invalid_punch_bounds(self):
        for bounds in ((0, 0), (500, 400), (-1, 200), (0, None), (None, 20), (1.2, 300)):
            with self.assertRaises(MidiError):
                CaptureBuffer(480, punch_start=bounds[0], punch_end=bounds[1])

    def test_punch_end_exclusive(self):
        capture = CaptureBuffer(480, 120, 0, 0, 480)
        self.assertTrue(capture.feed(b'\xc0\x05', 0))
        self.assertFalse(capture.feed(b'\xc0\x06', .5))
        self.assertEqual(len(capture.events()), 1)

class RecordingStopTests(unittest.TestCase):
    def test_finish_closes_held_note_at_stop_tick(self):
        capture = CaptureBuffer(480, bpm=120)
        capture.feed(b'\x90\x3c\x64', 0.25)
        events = capture.events(stop_tick=480)
        self.assertEqual([(e.tick, e.status, e.data) for e in events],
                         [(240, 0x90, b'\x3c\x64'), (480, 0x80, b'\x3c\x00')])

    def test_finish_preserves_released_notes(self):
        capture = CaptureBuffer(480)
        capture.feed(b'\x90\x3c\x64', 0)
        capture.feed(b'\x80\x3c\x00', 0.5)
        self.assertEqual(len(capture.events(stop_tick=960)), 2)

    def test_multiple_held_notes(self):
        capture = CaptureBuffer(480)
        capture.feed(b'\x90\x3c\x64', 0)
        capture.feed(b'\x90\x3c\x64', 0.1)
        capture.feed(b'\x90\x40\x64', 0.2)
        offs = [(e.tick, e.data[0]) for e in capture.events(stop_tick=480) if e.status == 0x80]
        self.assertEqual(offs, [(480, 60), (480, 60), (480, 64)])

    def test_stop_before_last_event_cannot_reverse_time(self):
        capture = CaptureBuffer(480)
        capture.feed(b'\x90\x3c\x64', 1)
        self.assertEqual(capture.events(stop_tick=0)[-1].tick, 960)

    def test_invalid_stop_tick(self):
        capture = CaptureBuffer(480)
        for value in (-1, 1.5, True, 0x10000000):
            with self.assertRaises(MidiError):
                capture.events(stop_tick=value)


class TempoMapRecordingTests(unittest.TestCase):
    def make_song(self):
        from midi import Event, Track, Song
        return Song(1, 480, [Track([
            Event(0, 0xff, (500000).to_bytes(3, 'big'), 0x51),
            Event(480, 0xff, (1000000).to_bytes(3, 'big'), 0x51),
            Event(960, 0xff, (250000).to_bytes(3, 'big'), 0x51),
        ])])

    def test_follow_tempo_changes(self):
        from midi_recording import SongTempoClock
        clock = SongTempoClock(self.make_song())
        self.assertEqual([clock.tick_at(t) for t in (0, .5, 1, 1.5, 1.75)],
                         [0, 480, 720, 960, 1440])

    def test_start_inside_tempo_segment(self):
        from midi_recording import SongTempoClock
        clock = SongTempoClock(self.make_song(), start_tick=720)
        self.assertEqual(clock.tick_at(0), 720)
        self.assertEqual(clock.tick_at(.5), 960)
        self.assertEqual(clock.tick_at(.75), 1440)

    def test_capture_uses_song_tempo(self):
        song = self.make_song()
        capture = CaptureBuffer(480, song=song)
        capture.feed(b'\x90\x3c\x64', .75)
        capture.feed(b'\x80\x3c\x00', 1.5)
        self.assertEqual([e.tick for e in capture.events()], [600, 960])

    def test_invalid_clock_inputs(self):
        from midi_recording import SongTempoClock
        clock = SongTempoClock(self.make_song())
        for value in (-1, float('nan'), float('inf'), True):
            with self.assertRaises(MidiError):
                clock.tick_at(value)
        with self.assertRaises(MidiError):
            CaptureBuffer(240, song=self.make_song())

    def test_same_tick_tempo_changes_last_wins(self):
        from midi import Event
        from midi_recording import SongTempoClock
        song = self.make_song()
        song.tracks[0].events.append(Event(480, 0xff, (750000).to_bytes(3, 'big'), 0x51, 1))
        clock = SongTempoClock(song)
        self.assertEqual(clock.tick_at(.5), 480)
        self.assertEqual(clock.tick_at(1.25), 960)

class SharedTransportTests(unittest.TestCase):
    def test_recorder_accepts_shared_epoch(self):
        from midi_recording import MidiRecorder
        with patch('midi_recording.threading.Thread') as thread, patch('midi_recording.time.monotonic', return_value=100.0):
            recorder = MidiRecorder()
            recorder.start('Keyboard', 480, start_at=101.0)
            self.assertEqual(recorder._started_at, 101.0)
            thread.return_value.start.assert_called_once()

    def test_recorder_rejects_bad_epoch(self):
        from midi_recording import MidiRecorder
        for value in (float('nan'), -1, True, 'now'):
            with self.assertRaises(MidiError):
                MidiRecorder().start('Keyboard', 480, start_at=value)

    def test_player_uses_same_epoch(self):
        from midi_output import MidiPlayer
        from midi import Song, Track
        with patch('midi_output.threading.Thread') as thread:
            player = MidiPlayer()
            player.play(Song(1, 480, [Track([])]), 'Synth', start_at=123.5)
            self.assertEqual(thread.call_args.kwargs['args'][-1], 123.5)

    def test_player_rejects_bad_epoch(self):
        from midi_output import MidiPlayer
        from midi import Song, Track
        for value in (float('inf'), -1, True, 'now'):
            with self.assertRaises(MidiError):
                MidiPlayer().play(Song(1, 480, [Track([])]), 'Synth', start_at=value)


class LatencyCompensationTests(unittest.TestCase):
    def test_positive_latency_moves_event_earlier(self):
        capture = CaptureBuffer(480, bpm=120, latency_ms=100)
        capture.feed(b'\x90\x3c\x64', .6)
        self.assertEqual(capture.events()[0].tick, 480)

    def test_negative_latency_moves_event_later(self):
        capture = CaptureBuffer(480, bpm=120, latency_ms=-50)
        capture.feed(b'\x90\x3c\x64', .5)
        self.assertEqual(capture.events()[0].tick, 528)

    def test_early_events_clamped_to_start(self):
        capture = CaptureBuffer(480, start_tick=960, latency_ms=200)
        capture.feed(b'\x90\x3c\x64', .05)
        self.assertEqual(capture.events()[0].tick, 960)

    def test_invalid_latency(self):
        for latency in (501, -501, float('nan'), True, '10'):
            with self.assertRaises(MidiError):
                CaptureBuffer(480, latency_ms=latency)

    def test_latency_uses_song_tempo_map(self):
        from midi import Song, Track, Event
        song = Song(1, 480, [Track([Event(480, 0xff, (1000000).to_bytes(3, 'big'), meta_type=0x51)])])
        capture = CaptureBuffer(480, song=song, latency_ms=100)
        capture.feed(b'\x90\x3c\x64', 1.1)
        self.assertEqual(capture.events()[0].tick, 720)


class RecordingChannelTests(unittest.TestCase):
    def test_filter_only_selected_input_channel(self):
        c = CaptureBuffer(480, input_channel=1)
        self.assertFalse(c.feed(b'\x90\x3c\x40', 0))
        self.assertTrue(c.feed(b'\x91\x3c\x40', 0))
        self.assertFalse(c.feed(b'\x80\x3c\x00', .1))
        self.assertTrue(c.feed(b'\x81\x3c\x00', .2))
        self.assertEqual([e.status for e in c.events()], [0x91, 0x81])

    def test_remap_notes_and_controllers(self):
        c = CaptureBuffer(480, output_channel=9)
        c.feed(b'\x92\x3c\x40', 0)
        c.feed(b'\xb2\x07\x64', .1)
        c.feed(b'\x82\x3c\x00', .2)
        self.assertEqual([e.status for e in c.events()], [0x99, 0xb9, 0x89])

    def test_filter_before_remapping(self):
        c = CaptureBuffer(480, input_channel=2, output_channel=5)
        self.assertFalse(c.feed(b'\x95\x3c\x40', 0))
        self.assertTrue(c.feed(b'\x92\x3c\x40', 0))
        self.assertEqual(c.events()[0].status, 0x95)

    def test_synthetic_note_off_uses_remapped_channel(self):
        c = CaptureBuffer(480, output_channel=3)
        c.feed(b'\x90\x3c\x64', 0)
        self.assertEqual(c.events(stop_tick=480)[-1].status, 0x83)

    def test_invalid_channels(self):
        for value in (-1, 16, 1.0, True, '1'):
            with self.assertRaises(MidiError):
                CaptureBuffer(480, input_channel=value)
            with self.assertRaises(MidiError):
                CaptureBuffer(480, output_channel=value)

class MonitorTests(unittest.TestCase):
    def test_monitor_port_validation(self):
        from midi_recording import MidiRecorder
        for port in ('', '   ', 123):
            with self.assertRaises(MidiError):
                MidiRecorder().start('Keyboard', 480, monitor_port=port)

    def test_monitor_uses_record_channel_and_sends_note_off_on_stop(self):
        from midi_recording import MidiRecorder, CaptureBuffer
        class Port:
            def __init__(self, messages=()):
                self.messages = list(messages)
                self.sent = []
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def iter_pending(self):
                messages, self.messages = self.messages, []
                return messages
            def send(self, msg): self.sent.append(msg)
        class Message:
            def __init__(self, data=None, *, channel=0, note=0, velocity=0):
                self.data = bytes((0x80 | channel, note, velocity)) if data == "note_off" else bytes(data)
            def bytes(self): return list(self.data)
            @classmethod
            def from_bytes(cls, data): return cls(data)
        class Mido:
            pass
            def set_backend(self, name): pass
            def open_input(self, name): return input_port
            def open_output(self, name): return output_port
        Mido.Message = Message
        input_port = Port([Message((0x90, 60, 100))])
        output_port = Port()
        recorder = MidiRecorder()
        recorder._started_at = 10.0
        recorder._stop.set()
        with patch.dict(sys.modules, {'mido': Mido()}), patch('midi_recording.time.monotonic', return_value=10.0):
            recorder._run('Keyboard', CaptureBuffer(480, output_channel=4), 'Output')
        self.assertEqual(output_port.sent[0].data, b'\x94\x3c\x64')
        self.assertEqual(output_port.sent[1].data, b'\x84\x3c\x00')

    def test_monitor_ignores_filtered_channel(self):
        from midi_recording import MidiRecorder, CaptureBuffer
        class Message:
            def bytes(self): return [0x91, 60, 100]
        class Port:
            def __init__(self): self.sent = []
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def iter_pending(self): return [Message()] if not hasattr(self, 'done') and setattr(self, 'done', True) is None else []
            def send(self, message): self.sent.append(message)
        incoming, outgoing = Port(), Port()
        class Mido:
            def set_backend(self, name): pass
            def open_input(self, name): return incoming
            def open_output(self, name): return outgoing
        recorder = MidiRecorder()
        recorder._started_at = 10
        recorder._stop.set()
        with patch.dict(sys.modules, {'mido': Mido()}), patch('midi_recording.time.monotonic', return_value=10):
            recorder._run('Keyboard', CaptureBuffer(480, input_channel=0), 'Output')
        self.assertEqual(outgoing.sent, [])
