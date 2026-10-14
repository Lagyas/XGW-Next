"""Routed loop wrap restores channel and held-note state at L."""
from midi import Song, Track, Event
from loop_boundary import routed_loop_prefix


def test_program_bank_restored_on_wrap():
    song = Song(1, 480, [Track([
        Event(0, 0xc0, bytes([8])), Event(10, 0xb0, bytes([32, 5])),
        Event(20, 0xb0, bytes([0, 63]))])])
    assert routed_loop_prefix(song, {0: ('B', 3)}, 'A', 30) == [
        (0.0, 'B', bytes([0xb3, 0, 63])),
        (0.0, 'B', bytes([0xb3, 32, 5])),
        (0.0, 'B', bytes([0xc3, 8]))]


def test_held_note_restored_on_wrap():
    song = Song(1, 480, [Track([
        Event(10, 0x90, bytes([60, 90])), Event(70, 0x80, bytes([60, 0]))])])
    assert routed_loop_prefix(song, {0: ('B', 2)}, 'A', 40) == [
        (0.0, 'B', bytes([0x92, 60, 90]))]


def test_events_at_left_not_duplicated():
    song = Song(1, 480, [Track([Event(40, 0x90, bytes([61, 90]))])])
    assert routed_loop_prefix(song, {}, 'A', 40) == []


def test_disabled_tracks_not_chased():
    song = Song(1, 480, [Track([Event(0, 0xc0, bytes([1]))]),
                         Track([Event(0, 0xc0, bytes([2]))])])
    assert routed_loop_prefix(song, {0: ('A', 0), 1: ('B', 1)}, 'A', 10, {1}) == [
        (0.0, 'B', bytes([0xc1, 2]))]
