"""Yamaha XGX-9903R XG export regression checks (stages 167–170)."""
import pytest
from midi import Song, Track, Event, MidiError
from xg_export import export_xg, XG_SYSTEM_ON
from xg_sysex import decode_parameter_change


def events(song):
    return [e for track in song.tracks for e in track.events]


def make_song():
    return Song(1, 480, [Track([
        Event(0, 0xff, bytes((3, 2, 24, 8)), 0x58),
        Event(0, 0xb0, bytes((0, 40))),
        Event(0, 0xb0, bytes((32, 1))),
        Event(0, 0xc0, bytes((56,))),
        Event(0, 0xb0, bytes((7, 83))),
        Event(0, 0x90, bytes((60, 100))),
        Event(240, 0x80, bytes((60, 0))),
    ])])


def test_setup_length_from_opening_meter_and_source_unchanged():
    song = make_song()
    before = song.to_bytes()
    out = export_xg(song, 2)
    assert next(e.tick for e in events(out) if e.status == 0x90) == 1440
    assert song.to_bytes() == before
    assert Song.from_bytes(out.to_bytes()).fmt == 1


def test_bank_program_and_volume_order_preserved():
    out = export_xg(make_song())
    part = [e for e in events(out) if e.status in (0xb0, 0xc0)]
    bank_msb = next(e for e in part if e.status == 0xb0 and e.data[0] == 0)
    bank_lsb = next(e for e in part if e.status == 0xb0 and e.data[0] == 32)
    program = next(e for e in part if e.status == 0xc0)
    volume = next(e for e in part if e.status == 0xb0 and e.data[0] == 7)
    assert bank_msb.data[1] == 40 and bank_lsb.data[1] == 1
    assert program.data == bytes((56,)) and volume.data[1] == 83
    assert bank_msb.tick < bank_lsb.tick < program.tick < volume.tick < 1440
    assert len([e for e in part if e.status == 0xb0 and e.data[0] == 7]) == 1


def test_xg_effect_types_inserted_and_roundtrip():
    out = Song.from_bytes(export_xg(make_song()).to_bytes())
    sysex = [e for e in events(out) if e.status == 0xf0]
    assert sum(e.data == XG_SYSTEM_ON for e in sysex) == 1
    addresses = {decode_parameter_change(bytes((0xf0,)) + e.data)['address']
                 for e in sysex if decode_parameter_change(bytes((0xf0,)) + e.data)}
    assert {(2, 1, 0), (2, 1, 32), (2, 1, 64)} <= addresses


def test_existing_effect_type_is_not_duplicated():
    from xg_effects import XGEffects
    song = make_song()
    model = XGEffects()
    model.set_type('reverb', 2, 0)
    song.tracks[0].events.append(Event(0, 0xf0, model.message('reverb')[1:]))
    out = export_xg(song)
    reverb = [e for e in events(out) if e.status == 0xf0 and
              (decoded := decode_parameter_change(bytes((0xf0,)) + e.data)) and
              decoded['address'] == (2, 1, 0)]
    assert len(reverb) == 1
    assert reverb[0].data == model.message('reverb')[1:]


def test_reject_ambiguous_multiport_and_short_measure():
    song = make_song()
    song.tracks[0].events.append(Event(0, 0xff, b'\x01', 0x21))
    with pytest.raises(MidiError, match='Multiport'):
        export_xg(song)
    song = make_song()
    song.tracks[0].events[0].data = bytes((1, 7, 24, 8))
    with pytest.raises(MidiError, match='short'):
        export_xg(song)


def test_level_one_format_zero_and_part_split_level_two():
    song = Song(0, 480, [Track([Event(0, 0x90, b'\x3c\x64'),
                                 Event(0, 0x91, b'\x40\x64')])])
    assert Song.from_bytes(export_xg(song, 1).to_bytes()).fmt == 0
    out = Song.from_bytes(export_xg(song, 2).to_bytes())
    for track in out.tracks:
        assert len({e.status & 15 for e in track.events if 0x80 <= e.status <= 0xef}) <= 1
