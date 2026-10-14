from unittest.mock import patch
from midi import Song, Track, Event
from midi_output import MidiPlayer


def song():
    return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64')])])


def capture(**kwargs):
    player = MidiPlayer()
    with patch('midi_output.threading.Thread') as thread:
        player.play_routed(song(), {0: ('B', 2)}, 'A', **kwargs)
        return thread.call_args.kwargs['args']


def test_routed_countin_targets_default_click_port():
    first, _, _, _, ports, epoch = capture(count_in_bars=1, start_at=123.0)
    assert epoch == 123.0
    assert 'A' in ports and 'B' in ports
    assert any(offset < 0 and port == 'A' and data[0] == 0x99 for offset, port, data in first)
    assert any(offset == 0 and port == 'B' and data[0] == 0x92 for offset, port, data in first)


def test_routed_countin_custom_click_port():
    first, _, _, _, ports, _ = capture(count_in_bars=1, click_port='C')
    assert 'C' in ports
    assert all(port == 'C' for offset, port, _ in first if offset < 0)


def test_routed_no_countin_has_no_negative_events():
    first, _, _, _, _, _ = capture()
    assert all(offset >= 0 for offset, _, _ in first)


def test_routed_sysex_follows_track_port():
    s = Song(1, 480, [Track([Event(0, 0xf0, b'\x43\x10\x4c\x00\xf7')])])
    player = MidiPlayer()
    with patch('midi_output.threading.Thread') as thread:
        player.play_routed(s, {0: ('B', None)}, 'A', include_sysex=True)
    first = thread.call_args.kwargs['args'][0]
    assert any(port == 'B' and payload[0] == 0xf0 for _, port, payload in first)
