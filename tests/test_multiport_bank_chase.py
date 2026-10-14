"""Bank select must precede program change on each independently routed port."""
from midi import Song, Track, Event
from multiport_chase import chase_messages


def test_bank_select_msb_lsb_precede_program_change():
    track = Track([
        Event(0, 0xb0, bytes([32, 4])),
        Event(1, 0xc0, bytes([40])),
        Event(2, 0xb0, bytes([0, 63])),
    ])
    song = Song(1, 480, [track])
    assert chase_messages(song, {0: ('B', 2)}, 'A', 10) == [
        ('B', bytes([0xb2, 0, 63])),
        ('B', bytes([0xb2, 32, 4])),
        ('B', bytes([0xc2, 40])),
    ]


def test_bank_chase_keeps_ports_independent():
    song = Song(1, 480, [
        Track([Event(0, 0xb0, bytes([0, 1]))]),
        Track([Event(0, 0xb0, bytes([0, 2]))]),
    ])
    assert chase_messages(song, {0: ('A', 0), 1: ('B', 0)}, 'A', 1) == [
        ('A', bytes([0xb0, 0, 1])), ('B', bytes([0xb0, 0, 2]))
    ]
