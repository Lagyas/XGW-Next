"""Single-port loop wrap mirrors routed state reconstruction."""
from midi import Song, Track, Event
from loop_boundary import single_port_loop_prefix, routed_loop_prefix


def test_single_port_matches_routed_prefix():
    song = Song(1, 480, [Track([
        Event(0, 0xb0, bytes([0, 63])),
        Event(10, 0xb0, bytes([32, 5])),
        Event(20, 0xc0, bytes([8])),
        Event(25, 0x90, bytes([60, 99])),
        Event(90, 0x80, bytes([60, 0]))])])
    single = single_port_loop_prefix(song, 'A', 40)
    routed = routed_loop_prefix(song, {}, 'A', 40)
    assert single == [(offset, payload) for offset, _, payload in routed]
    assert single[-1] == (0.0, bytes([0x90, 60, 99]))


def test_single_port_does_not_restore_event_at_left():
    song = Song(1, 480, [Track([Event(40, 0x90, bytes([61, 90]))])])
    assert single_port_loop_prefix(song, 'A', 40) == []


def test_single_port_respects_channel_mask():
    song = Song(1, 480, [Track([
        Event(0, 0xc0, bytes([2])), Event(0, 0xc1, bytes([3])),
        Event(5, 0x90, bytes([60, 90])), Event(5, 0x91, bytes([62, 90]))])])
    assert single_port_loop_prefix(song, 'A', 10, enabled_channels={1}) == [
        (0.0, bytes([0xc1, 3])), (0.0, bytes([0x91, 62, 90]))]


def test_player_repeat_timeline_restores_held_notes(monkeypatch):
    import midi_output
    captured = {}
    class FakeThread:
        def __init__(self, target, args, daemon):
            captured['args'] = args
        def start(self):
            pass
    monkeypatch.setattr(midi_output.threading, 'Thread', FakeThread)
    song = Song(1, 480, [Track([
        Event(10, 0x90, bytes([60, 90])),
        Event(100, 0x80, bytes([60, 0]))])])
    player = midi_output.MidiPlayer()
    player.play(song, 'A', start_tick=30, loop_start=40, loop_end=80)
    repeat = captured['args'][3]
    assert repeat.count((0.0, bytes([0x90, 60, 90]))) == 1
