from midi import Event, Song, Track
from xws_import import track_setup_report, format_track_setup_report, import_xws
from pathlib import Path


def test_setup_last_observed_per_channel():
    song = Song(1, 480, [Track([
        Event(0, 0xb0, bytes([7, 100])),
        Event(10, 0xb0, bytes([7, 85])),
        Event(20, 0xc0, bytes([40])),
        Event(30, 0xb1, bytes([10, 64])),
        Event(40, 0xf0, b'\x43\x10\x4c'),
    ])])
    row = track_setup_report(song)[0]
    assert row['channels'] == {1: {'volume': 85, 'program': 41}, 2: {'pan': 64}}
    assert row['sysex_events'] == 1


def test_setup_ignores_note_data_and_does_not_invent_settings():
    song = Song(1, 480, [Track([Event(0, 0x90, bytes([60, 100]))]), Track([])])
    rows = track_setup_report(song)
    assert rows[0]['channels'] == {1: {}}
    assert rows[1]['channels'] == {}
    assert 'not XGworks mixer state' in format_track_setup_report(song)


def test_real_xws_setup_report_is_read_only():
    path = Path('/mnt/data/A Dream of a Dream.XWS')
    if not path.exists():
        return
    original = path.read_bytes()
    song = import_xws(path)
    report = format_track_setup_report(song)
    assert len(track_setup_report(song)) == 24
    assert 'Bass' in report and 'Synth' in report
    assert path.read_bytes() == original
